---
name: capture-knowledge
description: Use before finishing any task that produced new, durable knowledge (a decision, a contact/institution outcome, a processing method, a caveat) so it gets written to the right place instead of lost.
---

# capture-knowledge

새로 알게 된 지식 중 기억해야 할 것은 그 자리에서 기록한다.
나중에 몰아서 정리하지 않는다.
기록 대상은 네 조건을 모두 만족한다 — 새로 알게 됐고, 이후에도 유효하며, 미래 작업·판단에 영향을 주고, 기존 문서·코드만으로는 알기 어렵다.

## 먼저: 이게 지식인가 결정인가

- **결정**(무엇을 왜 이렇게 하기로 했는지)은 `knowledge/`에 쓰지 않는다.
  - 특정 처리 절차에 관한 것 → 그 절차를 담은 `.agents/skills/*/SKILL.md`에 규칙으로 추가한다.
  - 특정 코드 동작에 관한 것 → 그 코드의 docstring/주석에 근거를 남긴다.
  - 레포 전체에 걸치는 절대 규칙 → `AGENTS.md`에 한 줄로 추가한다.
  - 위 셋 중 하나다. `knowledge/`에 결정 문서를 새로 만들지 않는다.
- **순수 지식**(기관 문의 결과, 경험칙, 재사용 예시, 참고 연구)만 `knowledge/`에 쓴다.
- **데이터 자체에 관한 사실**(좌표계·컬럼 의미·결측값·정정 이력·기관 해명)은 STAC 메타데이터에 쓴다.

판단 기준: "이 데이터셋 하나에 대한 사실"이면 STAC, "특정 절차·코드의 이유"면 skill/코드, "여러 작업에 걸친 그 외 맥락"이면 `knowledge/`.

## `knowledge/`에 쓸 때

1. **위치를 고른다.** 관련 개념이 묶이면 하위 디렉토리를 만든다. 기존 문서에 이어지는 내용이면 새 파일 대신 기존 문서를 갱신한다.
2. **OKF frontmatter를 단다** (`type`은 `contact | heuristic | howto | reference` 중 하나).

   ```yaml
   ---
   type: heuristic
   title: <한 줄 제목>
   description: <한 문장 요약>
   tags: [<검색용 키워드>]
   timestamp: <오늘 날짜 ISO 8601>
   ---
   ```

   모든 필드는 한 줄짜리 `key: value`로 쓴다.
   유일한 예외는 `tags`이며 `[a, b, c]` 형태의 flat 리스트로만 쓴다 — `.agents/skills/recall-knowledge/list_knowledge.py`가 이 문법만 파싱한다.
3. **본문은 구조화한다.** 자유 산문보다 제목·목록·표·코드블록을 선호한다.
4. **링크를 건다.** 관련 문서는 `/`로 시작하는 경로로 연결한다(기준점은 `knowledge/`). 한 사실은 기준 문서 하나에만 적고, 다른 문서에서는 한 문장으로 관계만 적고 링크한다.

## skill/코드에 쓸 때

- skill 파일에 쓸 때도 위 frontmatter 대신 그 skill의 기존 구조(절차 목록)에 맞춰 규칙 하나를 추가한다. skill이 비대해지면 새 skill로 분리하고 원래 skill에서 링크한다.
- 코드에 쓸 때는 그 함수/모듈의 docstring에 "왜"를 한 문단으로 남긴다.

## 문체

간결이 기본이다.
결론과 근거만 남기고, 쓰는 사람이 거친 과정은 지운다.
번역투로 쓰지 않는다 — 대응하는 한국어가 있는 영어 명사를 그대로 쓰지 않는다(caveat→주의사항, placeholder→임시값 등).
STAC/코드 스펙 고유 개념어(asset, checksum 등)는 예외.
과거와 비교하려고 쓴 서술("검토했으나 채택하지 않았다")은 지우고 최종 상태만 남긴다.

검증은 키워드를 grep하는 게 아니라 처음부터 끝까지 소리 내어 읽어보는 것이다.

## 규약

- **개인정보 최소화**: 실명·이메일·전화보다 기관·부서 단위 귀속을 기본으로 한다.
- **경험칙은 중립·증거 기반**으로: "이 기관은 조작한다"(비난) 대신 "2019/2020 좌표계 불일치 확인됨"(증거).
- **포착은 진위를 보장하지 않는다.** 인용한 자료나 문의한 경로를 함께 남긴다.
