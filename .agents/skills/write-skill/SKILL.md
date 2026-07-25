---
name: write-skill
description: skill을 새로 만들거나 기존 skill을 고칠 때 따르는 저작 규약. `.agents/skills/`에 skill을 추가·수정하려 할 때 먼저 읽는다.
---

# write-skill

[skill](https://github.com/agentskills/agentskills/blob/main)을 쓸 때 지키는 규약.

## 규칙

1. **단일 책임 원칙**

    - 한 개의 skill은 한 개의 책임을 가짐
    - 여러 일을 담지 않음
    - 장황함을 피하고 명확·간결하게 작성

2. **이름은 동사형**

    - 스킬 이름은 `동사-목적어` 명령형 kebab-case로 지음 (예: write-python, route-task)
    - 스킬은 에이전트의 행동 단위이므로 이름도 행동으로 표현
    - 예외: `repo-rule`처럼 행동이 아닌 절대제약 진입점

3. **한국어 작성**

    - 한글로 작성
    - 코드 식별자 등 원문 유지가 필요한 경우는 예외
    - 문체·품질은 `../write-korean/SKILL.md`를 따름

4. **저장 위치**

    - 현재 저장소의 `.agents/skills/*/SKILL.md`에 저장

5. **frontmatter**

    - `name`·`description` frontmatter 필수 작성
    - `description` 필드는 라우팅에 사용되므로 "언제 발동하는가"를 정확히 작성

6. **참조**

    - skill은 다른 skill을 참조해 작업 절차를 엮을 수 있음
    - 참조 경로는 해당 `SKILL.md`가 있는 디렉터리를 기준으로 작성
    - 형제 skill은 `../<name>/SKILL.md`로 참조
    - skill 간 `순환참조` 금지

7. **지침 반복 금지**

    - 같은 지침을 여러 skill에 복사하지 않음
    - 지침은 한 skill에만 두고, 다른 skill은 참조(규칙 6)로 가져다 씀
