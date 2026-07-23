---
type: decision
title: cloudpathlib 기반 S3/R2 캐시 활용 — 다운로드는 S3Path 직접 노출, 업로드는 checksum 서버사이드 반영
description: geovars.pipeline이 boto3 직접 호출 대신 cloudpathlib(S3Client/S3Path)로 R2에 접근하도록 바꾼 결정. 다운로드는 S3Path를 그대로 노출해 read-through 캐시를 쓰고, 업로드는 cloudpathlib으로 1회만 전송한 뒤 checksum을 copy_from으로 서버사이드 반영하는 publish_asset()로 통합했다.
tags: [s3, r2, cloudpathlib, cache, pipeline, checksum, boto3, geovars-pipeline]
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
- 업로드는 `publish_asset(asset: pystac.Asset, key: str, write) -> str`(checksum 반환)로 통합했다. 다음 순서로 동작한다.
  1. `S3Path.open("wb")`로 `write(f)`를 실행해 cloudpathlib이 1회 업로드한다.
  2. 업로드 직후 로컬 캐시 파일(재다운로드 없음)에서 checksum(Multihash)을 계산한다.
  3. `path.client.s3.Object(bucket, key).copy_from(..., MetadataDirective="REPLACE")`로 S3 객체의 커스텀 메타데이터에 같은 checksum을 서버사이드로 반영한다.
  4. `FileExtension.ext(asset, add_if_missing=True).checksum`에 같은 값을 기록한다.
  - 이 함수가 예전 `upload_asset(key) -> checksum: str`을 대체한다.
  - `asset`은 호출 전에 이미 `item.add_asset(...)`로 owner가 있는 상태여야 한다. `FileExtension.ext(asset, add_if_missing=True)`는 스키마 URI를 owner(Item)의 `stac_extensions`에 등록하므로, owner 없는 Asset에 쓰면 `pystac.STACError`가 난다.
    - 애초엔 `publish_asset`이 `pystac.Asset`을 새로 만들어 반환하는 형태로 설계했으나, 이 owner 제약 때문에 실제 R2 실행에서 바로 실패해 지금 형태로 바꿨다.
    - 호출 순서는 항상 asset 생성 → `item.add_asset(...)` → `publish_asset(asset, key, write)`다.
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

## 기각한 대안

- boto3로 커스텀 `Path` 클래스 직접 구현 — cloudpathlib이 이미 푼 read-through 캐시 로직(mtime 비교)을 다시 짜는 셈이라 기각.
- `S3Client`를 서브클래싱해 `_upload_file`(비공식 내부 확장점)을 오버라이드, 업로드마다 자동으로 checksum 메타데이터를 심는 방식 — cloudpathlib 내부 구현에 결합돼 향후 버전업에서 깨질 위험이 있고, 계산된 checksum 값을 호출자에게 돌려주는 경로도 어색해 기각.
- cloudpathlib 없이 로컬에 쓰고 `client.client.put_object()`를 직접 한 번 호출하는 방식 — 실제 업로드 자체는 cloudpathlib에 맡기려는 요구와 맞지 않아 기각.

## 관련

- [/decisions/secrets-and-s3-client.md](/decisions/secrets-and-s3-client.md)
- [/decisions/reproducibility.md](/decisions/reproducibility.md)
- [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)
- [/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md)
