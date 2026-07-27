---
name: inspect-data-quality
description: 실제 데이터와 출처 문서를 조사하여 품질·한계·누락 정보와 분석 활용 판단에 필요한 맥락을 확보할 때 발동.
---

# inspect-data-quality

실제 데이터와 출처 문서를 조사하여 데이터의 품질·한계·분석 맥락을 확보한다.
데이터 특성에 맞는 reference를 고르고, 선택한 reference의 모든 질문을 조사한다.

기계적 전수 검증·불변식 검사는 이 skill의 범위가 아니다.

## 조사 및 검토 방법

1. 데이터 특성에 맞는 reference를 선택 (아래 표, 해당하면 여러 개)
2. 선택한 reference마다 서브에이전트로 나눠 조사. 메인 대화 컨텍스트를 아끼기 위함
3. 메인이 결과를 취합하고, 각 항목을 {필드 후보, link 후보, 한계·미확인} 중 하나로 분류

reference 사이에 같은 검토 주제를 중복하지 않는다. 한 주제는 한 reference에만 둔다.

## 산출물

조사 결과는 대화에만 두지 않는다.

- 다른 skill이 호출한 경우 — 분류 결과를 호출측이 반영함
- 단독 조사인 경우 — 정착 위치를 사용자에게 확인한 뒤에만 파일에 씀. 후보는 파이프라인 스크립트를 우선함. `stac-metadata/` JSON은 직접 고치지 않음. 파이프라인에 남기기로 하면 후속 파이프라인 작업으로 반영함

## reference

| 조건 | reference |
| --- | --- |
| 모든 데이터 | `references/common.yaml` |
| 외부에서 처음 가져오는 데이터 | `references/derived-data.yaml` |
| 공간 위치·범위가 있는 GIS 데이터 | `references/geospatial.yaml` |
| geometry 열이 있음 | `references/vector.yaml` |
| 래스터(격자)임 | `references/raster.yaml` |
| 행·열 구조의 표임 | `references/tabular.yaml` |

## reference 개선

새로운 데이터 유형이나 반복되는 문제가 발견되면, 다른 reference와 겹치지 않는 질문만 추가한다.
