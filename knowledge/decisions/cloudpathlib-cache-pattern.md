---
type: decision
title: cloudpathlib 기반 S3/R2 캐시 활용 — 다운로드는 S3Path 직접 노출, 업로드는 checksum 서버사이드 반영
description: geovars.pipeline이 boto3 직접 호출 대신 cloudpathlib(S3Client/S3Path)로 R2에 접근하도록 바꾼 결정. 다운로드는 S3Path를 그대로 노출해 read-through 캐시를 쓰고, 업로드는 publish_asset()으로 통합했다. publish_asset()은 checksum을 먼저 버퍼에서 계산한 뒤 mode="local"(R2 미접촉, 로컬 캐시만)/mode="remote"(원격 checksum이 같으면 스킵, 다르면 업로드+copy_from 서버사이드 반영)로 분기한다 — publish_asset() 계약의 canonical 문서.
tags: [s3, r2, cloudpathlib, cache, pipeline, checksum, boto3, geovars-pipeline, publish-asset]
timestamp: 2026-07-23
---

# cloudpathlib 기반 S3/R2 캐시 활용

[/decisions/secrets-and-s3-client.md](/decisions/secrets-and-s3-client.md)에 남아 있던 미해결 항목("`s3_cache_dir()`를 실제 `cloudpathlib.S3Client(local_cache_dir=...)` 기반으로 구현")을 해소한 기록이다.

## 결정

- `geovars.pipeline`은 boto3를 직접 호출하지 않고 cloudpathlib(`S3Client`/`S3Path`)로 R2에 접근한다.
- `s3_client()`는 호출마다 새로 만든다. 싱글턴으로 재사용하지 않는다.
  - 캐시는 client 인스턴스가 아니라 로컬 디스크(`local_cache_dir`)에 있어, client를 재사용해도 캐시 히트에는 영향이 없다.
- 다운로드는 별도 헬퍼 없이 `s3_path(key) -> S3Path`만 노출한다.
  - 소비 스크립트는 cloudpathlib의 `.open()`/`.read_bytes()`/`.download_to()`를 직접 쓴다.
  - 로컬 캐시가 필요한지 판단(로컬/클라우드 mtime 비교)은 cloudpathlib이 그대로 한다.
- 로컬 캐시 경로는 cloudpathlib이 관리하는 구조(`S3Path.fspath`, `<local_cache_dir>/<bucket>/<key>`)를 그대로 쓴다.
  - 기존에 직접 짠 `s3_cache_path(key)`(버킷 세그먼트 없는 `.cache/s3/<key>` 구조)는 폐기했다.
  - bare 로컬 경로가 필요하면 `Path(s3_path(key).fspath)`로 얻는다.
- 업로드는 `publish_asset(asset: pystac.Asset, key: str, write, mode: str = "remote") -> str`(checksum 반환)로 통합했다. 다음 순서로 동작한다.
  1. `write(f)`를 **먼저 `io.BytesIO()` 버퍼에** 실행하고, 그 바이트로 checksum(Multihash)을 계산한다.
  2. `mode`로 분기한다(아래 "mode 파라미터" 참고).
  3. 어느 mode든 `FileExtension.ext(asset, add_if_missing=True).checksum`에 같은 값을 기록한다.
  - 이 함수가 예전 `upload_asset(key) -> checksum: str`을 대체한다.
  - `asset`은 호출 전에 이미 `item.add_asset(...)`로 owner가 있는 상태여야 한다. `FileExtension.ext(asset, add_if_missing=True)`는 스키마 URI를 owner(Item)의 `stac_extensions`에 등록하므로, owner 없는 Asset에 쓰면 `pystac.STACError`가 난다.
    - 애초엔 `publish_asset`이 `pystac.Asset`을 새로 만들어 반환하는 형태로 설계했으나, 이 owner 제약 때문에 실제 R2 실행에서 바로 실패해 지금 형태로 바꿨다.
    - 호출 순서는 항상 asset 생성 → `item.add_asset(...)` → `publish_asset(asset, key, write)`다.

### 스트리밍 → 버퍼링 전환

- 최초 구현은 `S3Path.open("wb")`로 `write(f)`를 스트리밍 실행해 cloudpathlib이 1회 업로드하고, 업로드 직후 로컬 캐시 파일에서 checksum을 계산했다.
- 지금은 `write()`를 **먼저 `io.BytesIO()`에 실행**해 checksum부터 계산한 뒤 mode를 분기한다.
  - 이유: `mode="remote"`의 스킵-if-match 판단(원격에 같은 checksum이 이미 있으면 업로드 자체를 생략)은 **업로드 전에** checksum을 알아야 가능하다. 스트리밍은 "쓰면서 계산"이라 업로드가 끝나야 checksum이 나와, 스킵 여부를 업로드 전에 결정할 수 없었다.
  - 대가: 큰 파일도 `io.BytesIO()`에 전량 버퍼링한다(스트리밍 시절엔 없던 메모리 사용). `sgis-adm-boundary`의 zip 크기(28~95MB)에서는 무시할 만한 트레이드오프로 판단했다 — 훨씬 큰 asset이 나오면 재검토한다.

### `mode` 파라미터 — local/remote

- `mode="remote"`(기본): `remote_checksum(key)`로 원격 커스텀 메타데이터의 checksum을 HEAD 요청만으로 읽어 계산한 checksum과 같으면 **업로드를 생략**한다. 다르면(또는 원격에 없으면, 즉 `None`) 기존 흐름대로 `S3Path.open("wb")`로 업로드한 뒤 `copy_from(..., MetadataDirective="REPLACE")`로 checksum을 서버사이드 메타데이터에 반영한다.
- `mode="local"`: R2를 **전혀 건드리지 않는다**. `s3_cache_dir() / bucket / key`(cloudpathlib 관례와 같은 구조)에 로컬 캐시 파일만 쓴다.
  - 이 경로는 `s3_cache_dir() / bucket / key`로 **직접 계산**한다. `s3_path(key).fspath`는 쓰지 않는다 — `S3Path`는 lazy라 `.fspath` 접근이나 파일 존재 확인이 cloudpathlib 내부에서 원격 HEAD/다운로드를 트리거할 수 있어, "R2 미접촉"이라는 mode의 계약을 깰 위험이 있다.
  - 빠른 개발 반복(실제 R2 업로드 없이 파이프라인 로직을 반복 실행)이 목적이며, 이 상태로 발행됐다고 볼 수 없다. 처리 스크립트의 `verify_uploaded` 단계가 이후 반드시 실패해 이를 강제한다(세부는 pipeline-architecture.md).
- `remote_checksum(key: str) -> str | None`: R2 객체의 커스텀 메타데이터 `checksum`을 HEAD 요청(`.metadata` 접근이 트리거)만으로 읽는다. 본문 다운로드는 없다. 객체가 없으면(404/NoSuchKey) `None`.
  - `publish_asset(mode="remote")`의 스킵 판단과, 처리 스크립트의 `verify_uploaded` 단계(mode 무관 항상 실행, pipeline-architecture.md 참고)가 이 헬퍼를 공유한다.
- `boto3`는 `pyproject.toml`의 `pipeline`/`all` extra에서 직접 명시하지 않는다. `cloudpathlib[s3]`가 이미 전이 의존성으로 관리한다.
  - `geovars.pipeline`의 import guard도 `boto3` 대신 `cloudpathlib`로 바꿨다.
- 캐시 무효화(mtime 비교)와 checksum(Multihash) 검증은 서로 다른 계층으로 다룬다.
  - mtime 비교는 "다시 받아야 하나"를 판단하는 순수 성능 문제이고, 진위 검증은 항상 STAC `file:checksum` 대 실제 바이트 해시다([/decisions/reproducibility.md](/decisions/reproducibility.md)).
  - CLAUDE.md의 "정정은 새 version으로 발행, in-place 금지" 규칙 때문에 한번 발행된 key는 write-once라, mtime 비교가 헷갈릴 상황(같은 key인데 내용이 바뀌는 경우) 자체가 구조적으로 거의 생기지 않는다.

## 근거

- cloudpathlib은 read-through 캐시(로컬/클라우드 mtime 비교)를 이미 구현해두고 있다. 이를 boto3로 다시 짜면 이미 검증된 로직의 재발명이다.
- 캐시 판단이 가끔 틀려도 안전한 이유는 checksum이 별도 계층에서 진위를 보장하기 때문이다. 그래서 캐시 라이브러리의 mtime 판단을 우리가 더 정교하게 만들 필요가 없다.
- checksum은 파일마다 값이 달라 client 생성 시 정적으로 고정하는 `extra_args`로는 넣을 수 없다. `copy_from`은 R2 내부에서 일어나는 서버사이드 복사라 로컬 회선(~10Mbps)으로 파일을 다시 보내지 않으므로, cloudpathlib의 업로드(1회)와 별개로 호출해도 네트워크 제약과 충돌하지 않는다.
- 실제 R2에 대고 `geovars-references` collection을 발행해 확인했다. `copy_from` + `MetadataDirective="REPLACE"`가 R2에서 정상 동작하고, 업로드된 오브젝트의 커스텀 메타데이터(`checksum`)가 STAC `file:checksum`과 정확히 일치했다(HEAD 요청으로 재확인).
- `mode` 파라미터를 추가한 계기는 `sgis-adm-boundary`(원본 zip 111개, 28~95MB)다. 매 개발 반복마다 실제 R2 업로드를 하면 느려서, R2를 건드리지 않는 `mode="local"` 경로가 필요했다.
- `mode="remote"`의 스킵-if-match는 이미 같은 checksum이 올라가 있는 asset을 재업로드하지 않게 해, 재실행이 잦은 개발 흐름에서 네트워크·시간을 아낀다. HEAD 요청(`remote_checksum`)만으로 판단하므로 스킵 여부를 알기 위해 본문을 내려받지 않는다.

## 기각한 대안

- boto3로 커스텀 `Path` 클래스 직접 구현 — cloudpathlib이 이미 푼 read-through 캐시 로직(mtime 비교)을 다시 짜는 셈이라 기각.
- `S3Client`를 서브클래싱해 `_upload_file`(비공식 내부 확장점)을 오버라이드, 업로드마다 자동으로 checksum 메타데이터를 심는 방식 — cloudpathlib 내부 구현에 결합돼 향후 버전업에서 깨질 위험이 있고, 계산된 checksum 값을 호출자에게 돌려주는 경로도 어색해 기각.
- cloudpathlib 없이 로컬에 쓰고 `client.client.put_object()`를 직접 한 번 호출하는 방식 — 실제 업로드 자체는 cloudpathlib에 맡기려는 요구와 맞지 않아 기각.
- `mode="local"`의 로컬 캐시 경로를 `s3_path(key).fspath`로 얻는 방식 — `S3Path`가 lazy라 `.fspath` 접근 자체가 cloudpathlib 내부에서 원격 HEAD/다운로드를 트리거할 수 있어 "R2 미접촉" 계약을 깰 위험이 있다. `s3_cache_dir() / bucket / key`로 직접 계산하는 쪽을 택했다.
- `mode`를 `pipeline/run.py`가 넘기는 CLI 플래그나 환경변수로 두는 방식 — "이 collection이 실제로 R2에 발행됐는가"는 실행 시점 선택이 아니라 collection의 상태이므로, 스크립트 모듈 상수 `PUBLISH_MODE`로 두어 발행 승인 이력이 git diff·커밋에 남게 했다(세부는 pipeline-architecture.md·write-pipeline-script 스킬).
- checksum을 스트리밍 도중(업로드하면서) 계산해 스킵 판단은 별도 사전 HEAD로만 하는 방식 — checksum 계산 로직이 스킵 경로와 업로드 경로로 이원화돼 오히려 복잡해져 기각. 버퍼링해 한 번에 계산하는 지금 방식이 더 단순하다.

## 관련

- [/decisions/secrets-and-s3-client.md](/decisions/secrets-and-s3-client.md)
- [/decisions/reproducibility.md](/decisions/reproducibility.md)
- [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)
- [/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md)
