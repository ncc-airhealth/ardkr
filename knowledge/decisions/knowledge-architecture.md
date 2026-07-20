---
type: decision
title: 지식 아키텍처 — STAC vs OKF 경계
description: 데이터에 관한 사실은 STAC이 SSOT, 그 외 간접 지식은 OKF. 충돌 시 우선순위와 provenance 위치까지 규정.
tags: [stac, okf, ssot, provenance]
timestamp: 2026-07-21
---

# 지식 아키텍처 — STAC vs OKF 경계

## 결정

- **데이터에 관한 사실·메타데이터의 SSOT는 STAC**이다 (Collection/Item JSON).
- **그 외 지식은 OKF**로 관리한다 — 의사결정 기록, 참고했던 연구, 데이터 처리 방법,
  예시 코드, 기관 문의 방법·이력 등 "데이터에 대한 간접 지식".
- 데이터에 관한 **해석적 caveat**(예: "2020년부터 UUID 체계가 바뀌어 이전 버전과 join
  금지")도 **STAC에 담는다**. 구조화가 가능하면 STAC extension을 적극 활용하고, 아니면
  `description`에 기록한다. 컬렉션 간 의존성·관계 정보도 STAC 메타데이터에 명시해
  검토 가능하게 한다.
- **공무원/담당기관 해명**은 데이터에 관한 1급 사실이므로 **STAC에 기록**한다.
  공식 배포 문서(.docx/.hwpx 등)는 collection의 **asset**으로 박제한다.

## 우선순위 규칙 (충돌 시)

- **STAC 필드 값 > shipped asset 문서.** asset으로 박제한 공식 문서는 *원본 증거*일 뿐,
  해석의 권위는 STAC 필드 값에 있다. (공식 문서가 오기인 경우가 잦기 때문)
- 담당기관 구두/서면 해명이 공식 문서와 충돌하면, **해명을 권위로** 삼고 그 판단 근거를
  provenance로 남긴다.

## Provenance 위치

- 정정의 근거("왜 shipped 문서와 다른가")는 **STAC 안에 인라인**(`description`)으로 둔다 —
  값과 근거가 같은 곳에 살아야 다리가 끊기지 않는다.
- 정해진 문법 없이 **자연어로 자유롭게 서술**한다 — 무엇을, 왜, 어떤 근거로 고쳤는지.
- 개인정보 최소화: 실명·이메일·전화보다 **기관·부서 단위 귀속**을 기본으로 한다
  (가벼운 서술 컨벤션, 강제 아님).

## 기각한 대안

- **caveat을 OKF에 두기** — 데이터를 STAC로 접근하는 에이전트가 OKF를 traverse할 이유가
  없어 "발견가능성 틈"이 생긴다. OKF는 링크 무결성도 보장하지 않는다(broken link도
  conformant). → 데이터 caveat은 STAC에 둔다.

## 관련

- [/principles.md](/principles.md)
- [/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)
- [/decisions/knowledge-capture.md](/decisions/knowledge-capture.md)

# Citations

1. OKF SPEC — https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
2. STAC 1.1.0 — https://stacspec.org / https://stac-extensions.github.io/
