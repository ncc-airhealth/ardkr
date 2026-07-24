---
name: write-pipeline-script
description: Use when writing or editing pipeline/process/<collection-id>.py processing scripts, adding a new collection, or refactoring an existing process script.
---

# write-pipeline-script

`pipeline/process/<collection-id>.py`는 파일명이 곧 collection id인 flat 처리 스크립트다.
사람이 열어서 검토하는 게 핵심 목적이라, 다른 어떤 코드보다 가독성을 우선한다.

이 파일은 진입점이다.
실제 규칙은 아래 skill로 나뉘어 있다.

- [pipeline-script-shape](../pipeline-script-shape/SKILL.md) — 파일 구조, 모듈 상수, `Processor` 클래스 규약.
- [pipeline-publish-verify](../pipeline-publish-verify/SKILL.md) — S3 업로드, 재검증, STAC 등록, 라이선스 확인.
- [resolve-data-discrepancy](../resolve-data-discrepancy/SKILL.md) — 코드북/문서와 실제 데이터가 다를 때 뭘 믿을지.
- [run-pipeline](../run-pipeline/SKILL.md) — 실제 실행 방법.
- [minimal-code](../minimal-code/SKILL.md) — 코드를 쓸 때 일반 규칙(재사용 우선 등). 단, `pipeline/process/*.py` 스크립트끼리는 재사용하지 않는다 — 이유는 pipeline-script-shape의 "스크립트 간 재사용 금지".

## 목표 사용자 경험

파일을 열면 이 순서로 읽힌다.

1. 상단 상수(`DESCRIPTION` 포함)를 보고 collection이 뭔지 파악한다.
2. `Processor.run()`을 보고 처리 흐름을 파악한다.
3. 궁금한 처리방식은 `run()`이 호출한 메서드의 정의를 따라가며 확인한다.

## 시작 전

- [recall-knowledge](../recall-knowledge/SKILL.md)로 다루려는 기관·데이터셋 관련 과거 지식을 먼저 조회한다.
- 비슷한 기존 스크립트를 참고하되, 코드를 공유하거나 import하지 않는다(위 재사용 예외).

## 검증

- CI가 없으므로 검증은 실제로 스크립트를 돌려서 한다 — 절차는 [run-pipeline](../run-pipeline/SKILL.md).
- 데이터 본문(`@property`로 둔 하드코딩 데이터 등)을 고쳤다면 `VERSION`을 올린다. `ASSET_FILENAME`이 `f"...version={VERSION}/..."` 패턴이라 자동으로 새 key가 된다.

## 마칠 때

- 스크립트를 처음부터 끝까지 다시 읽으며 이 skill들의 규칙과 하나씩 대조한다(상수 배치·순서, `run()`이 조건·반복 없이 호출만 나열하는지, `EXPERIMENTAL`/`PUBLISH_MODE` 승인 여부, `evaluate_asset()`/`verify_uploaded()` 존재 여부). 처음 보는 사람 입장에서 읽는다.
- [capture-knowledge](../capture-knowledge/SKILL.md)로 이번 작업에서 생긴 새 지식을 남긴다.
- `geovars` 쪽 코드를 고쳤다면, 커밋 후 PEP723 헤더의 pin 커밋 해시를 갱신하고 `--relock`.
