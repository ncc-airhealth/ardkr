---
name: pipeline-publish-verify
description: Use when a pipeline/process/<collection-id>.py script needs to upload an asset to S3/R2, verify the upload, or register a STAC collection/item.
---

# pipeline-publish-verify

`pipeline/process/<collection-id>.py`가 asset을 업로드하고 STAC에 등록하는 단계.
파일 구조는 [pipeline-script-shape](../pipeline-script-shape/SKILL.md), 진입점은 [write-pipeline-script](../write-pipeline-script/SKILL.md).

## S3(R2) 업로드/다운로드

- 다운로드: `geovars.pipeline.s3_path(key) -> S3Path`를 그대로 써서 `.open()`/`.read_bytes()`/`.download_to()`를 호출한다. 별도 캐시 판단 로직을 만들지 않는다 — cloudpathlib이 로컬/클라우드 mtime 비교로 알아서 한다.
- 업로드: `geovars.pipeline.publish_asset(asset, key, write, mode=PUBLISH_MODE)`. 왜 이렇게 동작하는지(체크섬을 먼저 버퍼에서 계산하는 이유, `mode` 분기)는 `geovars/geovars/pipeline/__init__.py`의 `publish_asset` docstring이 SSOT다 — 여기서는 호출 순서만 규정한다.
  1. `pystac.Asset(...)` 생성.
  2. `item.add_asset("<name>", asset)`로 owner를 먼저 확보한다. 순서를 어기면 `FileExtension.ext(asset, add_if_missing=True)`가 `pystac.STACError`를 낸다.
  3. `publish_asset(asset, key, write=lambda f: ..., mode=PUBLISH_MODE)`를 호출한다.
  - 이 호출을 감싸는 `Processor` 단계 메서드는 `publish_asset`이 아니라 `upload_asset`처럼 다른 이름을 쓴다 — 임포트한 함수 이름과 겹치면 "업로드(스토리지 계층)"와 "게시(STAC 카탈로그 계층)"가 헷갈린다.
- 원격 checksum만 확인(다운로드 없이): `geovars.pipeline.remote_checksum(key) -> str | None`.

## `evaluate_asset()` — 업로드 재검증

CI가 없으므로, 업로드가 실제로 성공했고 로컬 캐시가 read-through로 동작하는지 스크립트 스스로 확인한다.

```python
def evaluate_asset(self) -> None:
    if PUBLISH_MODE == "local":
        print(f"[{COLLECTION_ID}] local 모드 — 재검증 스킵(원격 미접촉)")
        return

    path = s3_path(ASSET_FILENAME)
    cache_file = Path(path.fspath)
    mtime_before = cache_file.stat().st_mtime if cache_file.exists() else None

    data = path.read_bytes()
    if multihash_sha256(data) != self.checksum:
        raise ValueError(f"재다운로드한 asset의 checksum이 기록값과 다릅니다: key={ASSET_FILENAME}")

    mtime_after = cache_file.stat().st_mtime
    if mtime_before != mtime_after:
        raise ValueError(f"asset을 로컬 캐시 대신 재다운로드했습니다: key={ASSET_FILENAME}")
```

재읽기+checksum 일치, 그리고 읽기 전후 캐시 파일 mtime이 그대로인지(재다운로드 안 했는지) 확인한다.
둘 중 하나라도 실패하면 예외를 던져 실행 자체를 실패시킨다.

## `verify_uploaded()` — 실제 R2 발행 확인

`PUBLISH_MODE`와 무관하게 파이프라인 마지막에 항상 실행한다 — "이 asset이 실제로 R2에 존재하는가" 자체를 확인한다.

```python
def verify_uploaded(self) -> None:
    actual = remote_checksum(ASSET_FILENAME)
    if actual != self.checksum:
        raise ValueError(
            f"[{COLLECTION_ID}] asset이 R2에 발행되지 않았거나 checksum이 다릅니다"
            f"(mode={PUBLISH_MODE}): key={ASSET_FILENAME} "
            f"expected={self.checksum} actual={actual}"
        )
```

`PUBLISH_MODE == "local"`로 돌렸다면 여기서 반드시 실패한다 — 버그가 아니라 "이 collection은 아직 발행되지 않았다"는 사실을 강제로 드러내는 안전장치다.
실제 발행하려면 `PUBLISH_MODE`를 `"remote"`로 flip하고(승인 주석 포함) 다시 실행한다.

item을 여러 개 만드는 collection은 모든 item의 모든 asset을 순회하며 문제를 모아 하나의 예외로 던진다 — `pipeline/process/sgis-adm-boundary.py`의 `verify_uploaded()` 참고.

## STAC 등록

- 코드북/asset 문서와 실제 데이터가 다르면 [resolve-data-discrepancy](../resolve-data-discrepancy/SKILL.md)로 뭘 믿을지 먼저 정한다.
- 등록 전, 원본 데이터의 라이선스·이용 약관을 확인한다. **확인이 끝나지 않았으면 등록을 보류한다** — `"proprietary"` 같은 임시값을 넣는 것은 확인을 생략해도 된다는 뜻이 아니다. 확인 결과는 `license` 필드에, 제약이 있으면 `description`에도 적는다.
- extension은 항상 pystac 공식 accessor로 적용한다: `XxxExtension.ext(obj, add_if_missing=True).필드 = ...`. 원본 dict/JSON을 직접 조작하지 않는다.
- `VersionExtension.ext(collection, add_if_missing=True)`에 `version`/`experimental`/`deprecated`를 모듈 상수 그대로 대입한다.
- 카탈로그 등록은 `geovars.catalog.register_collection(self.collection, VERSION)`로 한다. 버전 디렉터리 규칙(Hive 스타일 `version=<version>`), item 단위 asset 경로 규칙, pystac trailing-slash 버그 회피, `ensure_ascii=False` 재직렬화는 이 함수의 docstring(`geovars/geovars/catalog/__init__.py`)이 SSOT다. `catalog_root` 인자는 `pipeline/run.py`로 실행하면 생략해도 된다(cwd가 항상 레포 루트로 고정됨).

## 정정과 버전

- **해석-규정 필드**(`proj:code`, 컬럼 의미, 결측값 코드 등)는 버전 내에서 불변이다. 오기입 등 정정이 필요하면 새 버전을 발행한다 — [AGENTS.md](../../../AGENTS.md)의 절대 규칙.
- **`description` 같은 주석 필드는 in-place 수정이 허용된다.** git history가 이력을 보존하므로 감사가 깨지지 않는다.
- 새 버전 발행 시 옛 버전에 `deprecated: true`, `successor-version` 링크, 정정 사유를 붙인다(STAC Versioning Indicators extension) — 과거 사용자가 자기 pin 버전의 상태를 조회해 정정을 발견할 수 있게 한다.
