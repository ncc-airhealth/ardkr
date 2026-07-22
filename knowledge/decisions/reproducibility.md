---
type: decision
title: 재현성 — 처리 과정의 완전한 재현
description: 재현성은 처리 과정 기준. 원본·입력·코드 세 층을 pin하고, 원본·코드북을 박제하며 lock을 필수화한다. 데이터는 삭제하지 않고 냉동한다.
tags: [reproducibility, provenance, lock, r2, lineage]
timestamp: 2026-07-21
---

# 재현성 — 처리 과정의 완전한 재현

## 결정

재현성의 정의는 **처리 과정의 재현성**이다 — 같은 입력으로 처리 스크립트를 돌리면 같은 출력 collection이 나와야 한다.
이는 입력이 고정될 때만 성립하므로, 세 층을 모두 pin한다.

### 3층 pin

1. **원본 층** — 공공데이터 원본을 받은 순간 **R2에 스냅샷으로 박제**하고, 별도의 `source` collection으로 STAC에 등록한다 (원본 URL + 취득일 + checksum).
   - 처리 스크립트는 라이브 URL이 아니라 이 박제본을 입력으로 삼는다.
   - 공식 코드북/명세도 함께 박제한다 (검증 기준의 오라클; [/decisions/governance-and-review.md](/decisions/governance-and-review.md)).
   - 라이선스상 재배포 불가한 원본은 예외 — checksum + URL + 취득일만 기록하고 "재현 불가 구간"임을 메타데이터에 명시한다.
2. **입력 collection 층** — 해석-규정 필드가 버전 내 불변이므로 ([/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)), 입력을 **버전으로 pin**하면 해석이 고정된다.
   - 바이트는 STAC File Info extension의 **`file:checksum`(Multihash)**로 고정한다 — 이 값이 유일한 권위 있는 기준이다.
   - R2 업로드 시 **같은 checksum을 객체 커스텀 메타데이터**(`x-amz-meta-*`)에도 넣어, **HEAD 요청**(다운로드 없이)으로 빠른 1차 검증이 가능하게 한다.
      - 단 이는 우발적 드리프트만 잡는다 — 권위·정밀 검증은 STAC `file:checksum` 대 **실제 바이트 해시**로 한다.
      - (ETag는 멀티파트에서 단순 해시가 아니므로 checksum으로 쓰지 않는다.)
3. **코드 층** — 처리 스크립트(`pipeline/process/<collection-id>.py`)는 PEP 723 인라인 의존성을 선언하고 **스크립트별 lock을 필수로 커밋**한다.
   - 공용 유틸(`geovars`)은 git commit으로 pin한다.
   - 시스템 의존성(GDAL/GEOS/PROJ/uv)은 스크립트가 pin하는 **Docker+pixi 이미지 버전**으로 고정하고, 빌드된 이미지를 레지스트리에 보존한다.
   - 세부는 [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md).

### 강제

- lock은 "선택"이 아니라 **필수**다 — "선택"은 재현성이 무너지는 전형적인 경로다.
  - 단, **CI는 도입하지 않기로 확정**했다 ([/decisions/knowledge-capture.md](/decisions/knowledge-capture.md)).
  - 이 때문에 lock 필수는 **커밋 규칙(정책)으로만** 강제되고, "생성된 lock이 커밋됐는가"를 자동으로 확인하는 게이트는 두지 않는다.
  - 위반은 사후(재현 시도 실패, self-review)에나 발견된다 — 이 리스크는 의식적으로 감수한다.
  - 래퍼는 lock이 없으면 새로 생성하고 있으면 frozen 상태로 다뤄, 옛 스크립트를 다시 실행해도 pin이 무효화되지 않게 한다 ([/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)).

### 보존 정책 (삭제 금지)

- deprecated라고 해서 삭제해도 되는 것은 아니다.
  - deprecated collection은 이미 나간 분석·산출물이 입력으로 참조하고 있는 바로 그 데이터인 경우가 많다.
- **삭제 금지. deprecated는 R2 콜드 티어로 냉동**한다 — 비용은 낮추고 데이터는 보존한다.
  - 삭제는 재현성을 무너뜨린다.

## 왜

- 원본을 박제하지 않고 URL만 적으면, 공공기관이 파일을 교체하거나 내리는 순간 재현 불가능해진다.
- 재현성은 "할 수 있다"가 아니라, lock 커밋·이미지 보존 같은 **강제된 규칙**이 지켜질 때만 유지된다.

## 기각한 대안

- **버전 경로만으로 pin** — 메타데이터가 가변적이면 같은 경로가 다른 내용을 가리킬 수 있다.
  - 해석-규정 필드를 버전 내 불변으로 고정하여 해소.
- **deprecated 데이터 주기적 삭제** — 과거 산출물의 재현을 파괴한다.
  - 냉동으로 대체.
- **CI로 lock 커밋 강제** — 검토했으나 CI를 아예 도입하지 않기로 확정하면서 함께 기각.
  - 자동 게이트 없이 정책·self-review에 의존하는 리스크를 감수하기로 함 ([/decisions/knowledge-capture.md](/decisions/knowledge-capture.md)).

## 관련

- [/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)
- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)
