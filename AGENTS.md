# AGENTS.md

이 레포는 agent-native다. **3원칙**과 **절대규칙**을 따르며, 모든 작업은 **진입점**을 거친다.
어떤 에이전트 하네스를 쓰든 이 파일과 `.agents/skills/`만 읽으면 작업할 수 있어야 한다.

## 3원칙

- **agent-native**: 작업은 대화로, 지식은 레포 안에. 인간의 암묵지가 밖에 남지 않는다 (보안 정보는 예외).
- **catalog-in-repo**: 공간데이터 메타데이터는 STAC 1.1.0 JSON으로 `stac-metadata/`에 커밋한다.
- **reproducibility**: 데이터 처리 과정은 완전히 재현 가능해야 한다. 환경·의존성도 이 레포에서 관리한다.

## 절대규칙

세션의 첫 사용자 질문에서 `.agents/skills/repo-rule/SKILL.md`를 먼저 읽고, 명시된 규칙을 항상 따른다.

## 진입점

세션의 첫 사용자 질문에서, 또는 진행 중이던 작업과 다른 성격의 새 요청이 들어왔을 때 `.agents/skills/skill-router/SKILL.md`를 먼저 읽고 지시를 따른다.