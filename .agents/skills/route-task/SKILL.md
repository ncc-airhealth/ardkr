---
name: route-task
description: 세션의 첫 사용자 질문에서, 또는 진행 중이던 작업과 다른 성격의 새 요청이 들어왔을 때 사용하는 작업 라우팅 진입점.
---
# route-task

작업을 시작하기 전에 이 파일로 지금 할 일이 어떤 종류인지 파악하고, 맞는 skill로 넘어간다.

## 라우팅

- skill을 새로 만들거나 고치는 요청 → `.agents/skills/write-skill/SKILL.md`
- 파이프라인 처리 스크립트(`pipeline/process/*.py`)를 새로 쓰거나 고치는 요청 → `.agents/skills/write-pipeline-script/SKILL.md`
