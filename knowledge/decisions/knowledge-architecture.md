---
type: decision
title: 지식 아키텍처 — STAC vs OKF 경계
description: 데이터에 관한 사실과 메타데이터는 STAC에만 기록하고, 그 외 간접 지식은 OKF에 기록한다. 충돌 시 우선순위, provenance 위치, description 서술 관행(한국어·권장 템플릿)까지 규정.
tags: [stac, okf, ssot, provenance]
timestamp: 2026-07-21
---

# 지식 아키텍처 — STAC vs OKF 경계

## 결정

- 데이터에 관한 사실과 메타데이터는 STAC에만 기록한다(Collection/Item JSON).
- **그 외 지식은 OKF**로 관리한다 — 의사결정 기록, 참고했던 연구, 데이터 처리 방법, 예시 코드, 기관 문의 방법·이력 등 "데이터에 대한 간접 지식".
- 데이터에 관한 **해석적 주의사항**, 예를 들어 "2020년부터 UUID 체계가 바뀌어 이전 버전과 join 금지" 같은 사실도 **STAC에 담는다**.
  - 구조화가 가능하면 STAC extension을 적극 활용하고, 아니면 `description`에 기록한다.
  - 컬렉션 간 의존성·관계 정보도 STAC 메타데이터에 명시해 검토 가능하게 한다.
- **공무원/담당기관 해명**은 데이터에 관한 1급 사실이므로 **STAC에 기록**한다.
  - 공식 배포 문서(.docx/.hwpx 등)는 collection의 **asset**으로 보존한다.

## 우선순위 규칙 (충돌 시)

- **STAC 필드 값 > 배포된 asset 문서.**
  - asset으로 보존한 공식 문서는 *원본 증거*일 뿐, 해석의 권위는 STAC 필드 값에 있다.
  - 공식 문서에 오기가 잦기 때문이다.
- 담당기관 구두/서면 해명이 공식 문서와 충돌하면, **해명을 권위로** 삼고 그 판단 근거를 provenance로 남긴다.

## Provenance 위치

- 정정의 근거, 즉 왜 배포된 문서와 다른가는 **STAC 안에 인라인**(`description`)으로 둔다.
  - 값과 근거를 같은 곳에 두어야 연결이 끊기지 않는다.
- `description`은 **한국어로 작성**한다.
- 정해진 문법을 강제하지는 않는다.
  - 마커나 스키마 도입은 검토 후 기각했다.
  - 주의사항이나 정정을 적을 때는 아래 3칸 권장 템플릿을 따른다.
  - 권장일 뿐 강제는 아니고 CI 검증도 없다.
  - **대상** — 어떤 필드·기간·지역에 해당하는 주의사항인지
  - **내용·원인** — 무엇이 문제였고 왜 그런지
  - **근거** — 권위 있는 출처의 인용, 즉 코드북 조항이나 기관 해명의 결론과 근거다.
    - 문의 이력 자체는 OKF([/decisions/knowledge-capture.md](/decisions/knowledge-capture.md))에 남기고, 여기엔 결론과 근거만 적는다.
- 개인정보는 최소화한다.
  - 실명·이메일·전화보다 **기관·부서 단위 귀속**을 기본으로 하되, 이는 가벼운 서술 관행일 뿐 강제는 아니다.

## 기각한 대안

- **주의사항을 OKF에 두기** — 데이터를 STAC로 접근하는 에이전트가 OKF를 탐색할 이유가 없어 "발견가능성 틈"이 생긴다.
  - OKF는 링크 무결성도 보장하지 않으며, 깨진 링크도 OKF 규격을 준수한 것으로 간주된다.

## 관련

- [/principles.md](/principles.md)
- [/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)
- [/decisions/knowledge-capture.md](/decisions/knowledge-capture.md)

# Citations

1. OKF SPEC — https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
2. STAC 1.1.0 — https://stacspec.org / https://stac-extensions.github.io/
