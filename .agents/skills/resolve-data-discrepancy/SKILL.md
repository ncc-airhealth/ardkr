---
name: resolve-data-discrepancy
description: Use when a dataset's official codebook/asset documentation disagrees with the actual data, or when you need to contact an institution to clarify a discrepancy before writing STAC metadata.
---

# resolve-data-discrepancy

공식 코드북·asset 문서와 실제 데이터가 다를 때, 무엇을 믿고 STAC에 뭘 남길지 정하는 절차.

## 우선순위

- **최신 담당기관 해명 > 공식 코드북/원본 문서.** 기관이 문서와 다른 답을 주면 그 답을 따른다.
- 문서 버전이 여러 개면 **가장 최근에 담당기관이 확인해준 것**을 따른다 — 문서 발행일이 아니라 확인일 기준.
- 기관 해명을 구할 수 없으면, 실제 데이터 값과 문서 중 실제 값을 우선한다(문서가 오래돼 실측과 다를 가능성이 더 높다).

## 기관에 문의할 때

- 문의 경로(전화/이메일)와 날짜, 응답자 소속(부서 단위, 개인정보 최소화)을 기록해둔다 — [capture-knowledge](../capture-knowledge/SKILL.md)의 개인정보 규약을 따른다.
- 구두 답변도 유효한 근거다. 다만 나중에 뒤집힐 수 있으니 "당시 기준 확인됨"으로 남긴다.

## STAC에 남기기

- 최종 판단(코드북 대신 기관 해명을 따랐다는 사실과 근거)은 해당 collection/item의 `description`에 적는다. `knowledge/`에는 쓰지 않는다 — 이건 그 데이터셋 하나에 대한 사실이다.
- 판단이 바뀔 수 있는 사안이면 문의한 기관·날짜도 `description`에 함께 적어, 다음에 재확인할 때 누구에게 다시 물어야 하는지 알 수 있게 한다.

## 언제 이걸로도 부족한가

기관 해명 자체가 데이터의 해석을 바꾸는 정정이라면(예: 좌표계 오기 확인), 이 스킬은 "뭘 믿을지"만 정하고, 실제 반영은 [pipeline-publish-verify](../pipeline-publish-verify/SKILL.md)의 "정정과 버전" 절차(새 버전 발행)를 따른다.
