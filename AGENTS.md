# AGENTS.md

이 레포는 agent-native다 — 모든 작업은 에이전트와의 대화로 하고, 모든 지식은 레포 안에 둔다.
어떤 에이전트 하네스를 쓰든 이 파일과 `.agents/skills/`만 읽으면 작업할 수 있어야 한다.

## 세 가지 원칙

- **agent-native** — 작업은 대화로, 지식은 레포 안에. 인간의 암묵지가 밖에 남지 않는다 (보안 정보는 예외).
- **catalog-in-repo** — 공간데이터 메타데이터는 STAC 1.1.0 JSON으로 `stac-metadata/`에 커밋한다.
- **reproducibility** — 데이터 처리 과정은 완전히 재현 가능해야 한다. 환경·의존성도 이 레포에서 관리한다.

## 지식이 사는 곳 (역할 분리)

| 종류 | 위치 |
|---|---|
| 데이터에 관한 사실(좌표계, 컬럼 의미, 정정 이력, 기관 해명) | STAC (`stac-metadata/`) |
| 작업 절차와 그 이유 | `.agents/skills/` |
| 그 외 순수 지식(경험칙, 기관 문의 이력, 참고 자료) | `knowledge/` |
| 구현적 근거(왜 이 코드가 이렇게 짜였는지) | 해당 코드의 docstring/주석 |

의사결정은 `knowledge/`에 쓰지 않는다.
특정 절차에 관한 것이면 그 절차를 담은 skill에, 특정 코드 동작에 관한 것이면 그 코드에 남긴다.

## 상시 행동

- 작업 시작 전: `.agents/skills/recall-knowledge/SKILL.md`를 따라 관련 지식을 조회한다.
- 코드를 쓸 때: `.agents/skills/minimal-code/SKILL.md`를 따른다.
- 작업 마치기 전: 새 지식이 생겼으면 `.agents/skills/capture-knowledge/SKILL.md`를 따라 반영한다(완료 조건).

## 절대 규칙 (되돌릴 수 없음)

- 데이터·메타데이터 삭제 금지 (deprecated는 냉동).
- 데이터 해석을 바꾸는 정정은 in-place 금지, 새 version으로 발행.

## 레포 지도

```
geovars/          # Python 패키지 — pipeline/catalog/dashboard/modeling extras
pipeline/
  images/         # 시스템 환경(Docker+pixi), 날짜 버전별
  process/        # 처리 스크립트, collection id별 flat 파일
stac-metadata/    # STAC 카탈로그 JSON — 데이터 사실의 SSOT
.agents/skills/   # 작업 절차 — 여기서부터 시작 (<name>/SKILL.md, agentskills.io 형식)
knowledge/        # 순수 지식(OKF): STAC 스펙 참고자료, 경험칙, 문의 이력
```

새 collection을 추가하거나 처리 스크립트를 고치려면 `.agents/skills/write-pipeline-script/SKILL.md`부터 읽는다.
