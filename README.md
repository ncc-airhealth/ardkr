# geovars

> 연구팀을 위한 **agent-native 공간데이터 카탈로그 & 처리 파이프라인**.
> 주로 대한민국 공공 공간데이터를 재현 가능하게 가공하고, STAC으로 카탈로그화하며,
> 지리변수(geovariable) 계산을 지원합니다.

`geovars`는 두 가지를 하나의 레포에서 관리합니다.

- **데이터 카탈로그** — 공공데이터 원본을 수집·가공해 STAC Collection/Item으로
  메타데이터화하고, 데이터 자산은 오브젝트 스토리지(Cloudflare R2)에 둡니다.
- **지리변수 계산** — 카탈로그의 참조 데이터에 대해 포인트 데이터셋의 공간변수를
  계산하는 Python 라이브러리.

이 레포 자체가 **source of truth**입니다. 코드·메타데이터·처리 이력·의사결정이 모두
여기 담겨, 다른 사람이 오더라도 이 레포만으로 전체 맥락을 파악하고 재현할 수 있습니다.

## 설계 철학

| 원칙 | 의미 |
|---|---|
| **agent-native** | 모든 작업은 에이전트 하네스(Claude Code, Codex 등)와의 대화로 수행하고, 모든 지식은 이 레포 안에 존재합니다. |
| **catalog-in-repo** | 공간데이터 메타데이터를 STAC 1.1.0으로 관리하고, static STAC(JSON)을 git으로 직접 버전 관리합니다. |
| **reproducibility** | 데이터 처리 과정이 완전히 재현 가능합니다 — 같은 입력으로 처리하면 같은 출력이 나옵니다. |

배경과 상세 결정은 [`knowledge/`](knowledge/index.md)에 기록되어 있습니다.

## 저장소 구조

```
geovars/          # Python 패키지 (STAC 대시보드·파이프라인 유틸·카탈로그 검색·모델링)
pipeline/
  images/         # 시스템 환경 정의 (pixi + Dockerfile), 날짜 버전별
  process/        # 처리 스크립트 (collection id별 flat 파일)
stac-metadata/    # STAC 카탈로그 JSON (데이터 사실의 SSOT)
knowledge/        # OKF 기반 지식 (의사결정·문의 이력·처리법)
```

## 카탈로그 둘러보기

STAC 카탈로그는 JSON으로 이 레포에 커밋되며, 표준 STAC 도구로 탐색할 수 있습니다.

- [stac-browser](https://github.com/radiantearth/stac-browser)에 카탈로그 URL을 입력해
  Collection·Item을 시각적으로 탐색.
- 카탈로그(메타데이터)는 공개되어 있습니다. 각 collection당 **최신 버전**이 카탈로그에
  노출되고, 과거 버전 메타데이터는 이 레포에서 버전 경로로 조회할 수 있습니다.

## 데이터 접근

- **메타데이터**는 누구나 열람할 수 있습니다.
- **데이터 자산**(R2)에 접근하려면 자격증명이 필요합니다. 담당자에게 요청하세요.
  (보안서약 데이터 보호 및 스토리지 요청 비용 관리를 위한 접근 제어입니다.)

STAC asset의 `href`에는 R2 객체 key가 그대로 담겨 있어, 버킷/엔드포인트 설정만 결합하면
데이터 위치를 스스로 서술합니다.

## Collection 추가하기

데이터 처리는 다음 절차를 따릅니다.

1. collection 추가 요청을 정의합니다 (무엇을, 어떤 검증 기준으로).
2. 에이전트가 **검증 절차를 포함한** 처리 스크립트 `pipeline/process/<collection-id>.py`를
   작성합니다.
3. 담당자가 `pipeline/` 실행기(`pipeline/run.py`)로 스크립트를 실행합니다.

처리 스크립트는 ① collection 정의 → ② item/asset 로컬 프로세싱 → ③ 검증 →
④ R2 업로드 → ⑤ STAC 메타데이터 저장 순으로 진행합니다. Python 의존성은 PEP 723으로
스크립트마다 독립 선언하고 lock으로 고정합니다. 시스템 의존성(GDAL/GEOS/PROJ)은
스크립트가 지정한 **Docker+pixi 이미지 버전**으로 고정되며, 실행기(`pipeline/run.py`)가 해당
컨테이너 안에서 스크립트를 실행합니다. 세부는
[`knowledge/decisions/pipeline-architecture.md`](knowledge/decisions/pipeline-architecture.md).

## 지식 베이스

데이터에 관한 사실은 STAC 메타데이터가 SSOT이고, 그 외 지식(의사결정 기록, 참고연구,
처리 방법, 기관 문의 이력 등)은 [`knowledge/`](knowledge/index.md)에
[OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
형식으로 관리합니다.

## 재현성

- 공공데이터 원본과 코드북은 취득 시점에 스냅샷으로 박제해 `source` collection으로
  등록합니다.
- 데이터·메타데이터는 삭제하지 않습니다. 오래된 버전은 deprecated로 표시하고 콜드
  스토리지로 냉동합니다.
- 데이터 해석을 바꾸는 정정(예: 좌표계 오기)은 새 버전으로 발행합니다.

## 프로젝트 상태

활발히 개발 중입니다. 설계 결정은 [`knowledge/decisions/`](knowledge/decisions/index.md)에서
확인할 수 있습니다.

## 기여

작업은 에이전트 하네스와의 대화로 수행하고, 변경은 PR 리뷰를 거쳐 반영합니다.
새로 알게 된 지식(의사결정·기관 문의 결과·주의사항)은 작업을 마치기 전에
[`knowledge/`](knowledge/index.md)에 함께 기록합니다.
