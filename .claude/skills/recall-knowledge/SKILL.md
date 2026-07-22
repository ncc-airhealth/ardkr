---
name: recall-knowledge
description: >-
  작업을 시작하기 전에 레포의 knowledge 베이스(knowledge/ OKF 번들)에서 관련된 과거
  의사결정·기관 연락 이력·데이터 주의사항·불신 경험칙을 찾아본다. 데이터 처리,
  카탈로그 변경, 아키텍처 결정, 특정 기관/데이터셋을 다루는 작업을 시작할 때 사용한다.
---

# recall-knowledge

이 레포는 모든 지식을 레포 안에 둔다(agent-native).
어떤 작업이든 시작 전에 관련 지식을 먼저 조회한다.
그래야 과거 결정을 되풀이하거나 뒤엎지 않고 기존 맥락 위에서 작업할 수 있다.

## 언제 쓰나

- 새 collection을 추가하거나 기존 데이터를 가공하기 전
- 특정 기관·데이터셋(예: "국토부 건물통합정보")을 처음 다룰 때
- 아키텍처/운영 방식에 영향을 주는 결정을 내리기 전
- "이거 예전에 정한 것 같은데?" 싶은 순간

## 절차

1. **frontmatter를 조회한다.** 문서 목록은 손으로 쓴 목록이 아니라 스크립트로 조회한다.

   ```bash
   python3 .claude/skills/recall-knowledge/list_knowledge.py knowledge/decisions --type decision
   python3 .claude/skills/recall-knowledge/list_knowledge.py knowledge/ --tag <태그>
   ```

   `knowledge/principles.md`(상위 원칙)는 항상 직접 읽는다. 여기에 어긋나는 작업이면 멈추고 논의한다.

2. **키워드·태그로 검색한다.**
   - 다루려는 기관명, 데이터셋명, 개념(예: `proj:code`, `deprecated`, `checksum`, `provenance`, 좌표계, 결측값)으로 `knowledge/` 전체를 grep한다.
   - 각 문서 frontmatter의 `tags:`를 활용한다.

   ```bash
   grep -rin "<키워드>" knowledge/
   ```

3. **관련 결정을 읽는다.** 요약만 보지 말고 decision type 문서 본문의 결정 / 근거 / 기각한 대안 / 미해결을 확인한다.
   `/decisions/...` 경로로 연결된 링크를 따라간다.

4. **데이터에 관한 사실은 STAC에 있다.** 특정 데이터셋의 좌표계·컬럼 의미·정정 이력·기관 해명은 해당 collection의 STAC 메타데이터에서 확인한다.
   `description`에는 정정 내용이 자연어로 서술되어 있다. knowledge/는 그 외 간접 지식(처리법·문의 이력·경험칙·결정)만 담는다.

5. **찾은 것을 사용자에게 요약 보고한다.** 특히:
   - 지금 하려는 작업과 **충돌**하는 과거 결정
   - 해당 기관·데이터셋에 대한 **주의사항·경험칙**
   - 재사용할 수 있는 **처리법·연락 경로**
   - 관련된 **미해결** 항목

## 아무것도 없으면

관련 지식이 없다면 그 사실을 알리고 진행한다.
이번 작업에서 새 지식이 생기면 `capture-knowledge`로 반드시 남긴다.
