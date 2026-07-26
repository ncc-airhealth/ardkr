# ardkr

> 연구팀을 위한 **agent-native 공간데이터 카탈로그 & 처리 파이프라인**.
> 대한민국 공공 공간데이터를 재현 가능하게 가공한다.
> STAC으로 카탈로그화하고, 지리변수(geovariable) 계산을 지원한다.

`ardkr`는 두 가지를 한 레포에서 관리한다.

- **데이터 카탈로그** — 공공데이터 원본을 수집·가공해 STAC Collection/Item으로 메타데이터화함. 데이터 자산은 오브젝트 스토리지(Cloudflare R2)에 둠
- **지리변수 계산** — 카탈로그 참조 데이터로 포인트 데이터셋의 공간변수를 계산하는 Python 라이브러리

이 레포가 **source of truth**다.
코드·메타데이터·처리 이력·의사결정이 모두 여기 있다.
다른 사람이 와도 이 레포만으로 맥락을 파악하고 재현할 수 있다.
작업은 어떤 에이전트 하네스든 [`AGENTS.md`](AGENTS.md)를 읽고 시작한다.

## 설계 철학

| 원칙 | 의미 |
|---|---|
| **agent-native** | 작업은 에이전트 하네스(Claude Code, Codex 등)와의 대화로 수행함. 지식은 이 레포 안에 둠 |
| **catalog-in-repo** | 공간데이터 메타데이터를 STAC 1.1.0으로 관리함. static STAC(JSON)을 git으로 버전 관리함 |
| **reproducibility** | 데이터 처리가 완전히 재현 가능함. 같은 입력이면 같은 출력이 나옴 |

Analysis-ready data란 품질을 스스로 판정할 수 있게 만든 데이터다.
결함 없음이나 고품질을 약속한다는 뜻이 아니다.
알려진 결함·확인하지 못한 정보·판단에 필요한 맥락을 데이터와 STAC metadata가 함께 드러내야 한다.
그러면 사용자나 에이전트가 자기 분석에 쓸지 판단할 수 있다.
조사 절차는 [`inspect-data-quality`](.agents/skills/inspect-data-quality/SKILL.md)를 따른다.

작업 절차와 그 근거는 `.agents/skills/`에 있다.
그 외 지식(문의 이력·경험칙·참고자료)은 `knowledge/`에 있다.
내용은 에이전트에게 묻는다.

## 저장소 구조

```
ardkr/          # Python 패키지 (STAC 대시보드·파이프라인 유틸·카탈로그 검색·모델링)
pipeline/
  images/         # 시스템 환경 정의 (pixi + Dockerfile), 날짜 버전별
  process/        # 처리 스크립트 (collection id별 flat 파일)
stac-metadata/    # STAC 카탈로그 JSON (데이터 사실의 SSOT)
.agents/skills/   # 작업 절차와 그 근거 (<name>/SKILL.md)
knowledge/        # OKF 기반 지식 (문의 이력·경험칙·참고자료)
```

## 카탈로그 둘러보기

STAC 카탈로그는 JSON으로 이 레포에 커밋된다.
표준 STAC 도구로 탐색할 수 있다.

- [stac-browser](https://github.com/radiantearth/stac-browser)에 카탈로그 URL을 넣어 Collection·Item을 시각적으로 탐색함
- 카탈로그(메타데이터)는 공개됨. collection마다 **최신 버전**이 노출됨. 과거 버전 메타데이터는 이 레포의 버전 경로로 조회함

## 데이터 접근

- **메타데이터**는 누구나 열람할 수 있음
- **데이터 자산**(R2) 접근에는 자격증명이 필요함. 담당자에게 요청함. 보안서약 데이터 보호와 스토리지 비용 관리를 위한 접근 제어임

STAC asset의 `href`에는 R2 객체 key가 그대로 들어 있다.
버킷·엔드포인트 설정만 붙이면 데이터 위치를 스스로 서술한다.

## Collection 추가하기

데이터 처리는 다음 절차를 따른다.

1. collection 추가 요청을 정의함 (무엇을, 어떤 검증 기준으로)
2. 에이전트가 **검증 절차를 포함한** 처리 스크립트 `pipeline/process/<collection-id>.py`를 작성함
3. 담당자가 `pipeline/` 실행기(`pipeline/run.py`)로 스크립트를 실행함

처리 스크립트는 ① collection 정의 → ② item/asset 로컬 프로세싱 → ③ 검증 → ④ R2 업로드 → ⑤ STAC 메타데이터 저장 순으로 진행한다.
Python 의존성은 PEP 723으로 스크립트마다 독립 선언하고 lock으로 고정한다.
시스템 의존성(GDAL/GEOS/PROJ)은 스크립트가 지정한 **Docker+pixi 이미지 버전**으로 고정된다.
실행기(`pipeline/run.py`)가 그 컨테이너 안에서 스크립트를 실행한다.
세부는 [`.agents/skills/write-pipeline-script/SKILL.md`](.agents/skills/write-pipeline-script/SKILL.md).

## 지식 베이스

데이터에 관한 사실은 STAC 메타데이터가 SSOT다.
작업 절차와 그 근거는 `.agents/skills/`에 둔다.
그 외 순수 지식(참고연구, 처리 방법, 기관 문의 이력 등)은 `knowledge/`에 [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) 형식으로 관리한다.
내용은 에이전트에게 묻는다.

## 재현성

처리 환경 재현은 3층 pin(이미지+ardkr commit+PEP723 lock, 세부는 `pipeline/run.py`)이 담당한다.
원본 데이터 재현은 아래 스냅샷 보존이 담당한다.

- 공공데이터 원본과 코드북은 취득 시점에 스냅샷으로 박제해 `source` collection으로 등록함
- 데이터·메타데이터는 삭제하지 않음. 오래된 버전은 deprecated로 표시하고 콜드 스토리지로 냉동함
- 데이터 해석을 바꾸는 정정(예: 좌표계 오기)은 새 버전으로 발행함

