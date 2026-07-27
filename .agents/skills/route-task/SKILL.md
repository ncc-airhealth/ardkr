---
name: route-task
description: 세션의 첫 사용자 질문에서, 또는 진행 중이던 작업과 다른 성격의 새 요청이 들어왔을 때 사용하는 작업 라우팅 진입점.
---
# route-task

작업을 시작하기 전에 작업 종류를 파악하고 알맞은 skill로 이동한다.

## 라우팅

- skill을 새로 만들거나 고치는 요청 → `../write-skill/SKILL.md`
- 파이프라인 처리 스크립트(`pipeline/process/*.py`)를 새로 쓰거나 고치는 요청 → `../write-pipeline-script/SKILL.md`
- 실제 데이터·출처 문서의 품질·한계·누락 정보 조사 → `../inspect-data-quality/SKILL.md`
- STAC 메타데이터 내용 설계 (필드, links, description, providers, 라이선스 맥락) → `../design-stac-metadata/SKILL.md`
