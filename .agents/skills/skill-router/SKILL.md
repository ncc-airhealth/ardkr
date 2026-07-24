---
name: skill-router
description: Use at the start of any task in this repo to understand the repo's knowledge layout, the always-on checkpoints, and which skill to read next based on what the task actually is.
---

# skill-router

작업을 시작하기 전에 이 파일로 지금 할 일이 어떤 종류인지 파악하고, 맞는 skill로 넘어간다.
세 가지 원칙은 [AGENTS.md](../../../AGENTS.md) 참고.

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

- 작업 시작 전: [recall-knowledge](../recall-knowledge/SKILL.md)를 따라 관련 지식을 조회한다.
- 코드를 쓸 때: [minimal-code](../minimal-code/SKILL.md)를 따른다.
- 작업 마치기 전: 새 지식이 생겼으면 [capture-knowledge](../capture-knowledge/SKILL.md)를 따라 반영한다(완료 조건).
- skill을 추가/삭제/이름 변경했을 때: [manage-agent-dag](../manage-agent-dag/SKILL.md)로 참조 그래프를 갱신한다.

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

새 collection을 추가하거나 처리 스크립트를 고치려면 [write-pipeline-script](../write-pipeline-script/SKILL.md)부터 읽는다.
