---
name: recall-knowledge
description: Use before starting any work on this repo (new collection, data processing, catalog changes, or touching an institution/dataset for the first time) to check past decisions, caveats, and heuristics before acting.
---

# recall-knowledge

작업을 시작하기 전에 관련 지식을 먼저 찾는다.
그래야 과거 결정을 되풀이하거나 뒤엎지 않고 기존 맥락 위에서 작업할 수 있다.

## 언제 쓰나

- 새 collection을 추가하거나 기존 데이터를 가공하기 전.
- 특정 기관·데이터셋을 처음 다룰 때.
- "이거 예전에 정한 것 같은데?" 싶은 순간.

## 절차

1. **관련 skill을 읽는다.** 작업 절차와 그 이유는 이제 `knowledge/`가 아니라 `.agents/skills/*/SKILL.md`에 있다. 지금 하려는 작업과 겹치는 skill이 있으면 전문을 읽는다.
2. **관련 코드의 docstring/주석을 확인한다.** 구현적 근거(왜 이렇게 짜였는지)는 코드 자체에 있다. 예: `geovars/geovars/pipeline/__init__.py`, `geovars/geovars/catalog/__init__.py`.
3. **키워드로 `knowledge/`를 검색한다.** 순수 지식(경험칙·기관 문의 이력·참고 자료)이 남아 있는 곳이다.

   ```bash
   grep -rin "<키워드>" knowledge/
   python3 .agents/skills/recall-knowledge/list_knowledge.py knowledge/ --tag <태그>
   ```

4. **데이터에 관한 사실은 STAC에 있다.** 좌표계·컬럼 의미·정정 이력·기관 해명은 해당 collection의 STAC 메타데이터(`description`)에서 확인한다. 코드북과 다른 내용이 있으면 [resolve-data-discrepancy](../resolve-data-discrepancy/SKILL.md)를 참고한다.
5. **찾은 것을 사용자에게 요약 보고한다.** 특히 지금 작업과 충돌하는 과거 결정, 주의사항, 재사용할 처리법, 미해결 항목.

## 아무것도 없으면

그 사실을 알리고 진행한다.
새 지식이 생기면 [capture-knowledge](../capture-knowledge/SKILL.md)로 반드시 남긴다.
