# AGENTS.md

이 레포는 agent-native다 — 모든 작업은 에이전트와의 대화로 하고, 모든 지식은 레포 안에 둔다.
어떤 에이전트 하네스를 쓰든 이 파일과 `.agents/skills/`만 읽으면 작업할 수 있어야 한다.

## 세 가지 원칙

- **agent-native** — 작업은 대화로, 지식은 레포 안에. 인간의 암묵지가 밖에 남지 않는다 (보안 정보는 예외).
- **catalog-in-repo** — 공간데이터 메타데이터는 STAC 1.1.0 JSON으로 `stac-metadata/`에 커밋한다.
- **reproducibility** — 데이터 처리 과정은 완전히 재현 가능해야 한다. 환경·의존성도 이 레포에서 관리한다.

## 절대 규칙 (되돌릴 수 없음)

- 데이터·메타데이터 삭제 금지 (deprecated는 냉동).
- 데이터 해석을 바꾸는 정정은 in-place 금지, 새 version으로 발행.

## 다음 단계

작업을 시작하기 전에 `.agents/skills/skill-router/SKILL.md`를 읽고, 그에 따라 사용자의 작업을 이해하고 정의해라.
