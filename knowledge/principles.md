---
type: principle
title: 세 가지 창립 원칙
description: 이 레포의 존재 이유이자 모든 설계 결정의 상위 기준인 agent-native, catalog-in-repo, reproducibility.
tags: [foundation, agent-native, stac, reproducibility]
timestamp: 2026-07-20
---

# 세 가지 창립 원칙

이 레포는 연구팀의 공간데이터 처리과정과 카탈로그를 관리한다. 모든 하위 결정은
아래 세 원칙에 종속된다.

## 1. agent-native

모든 작업은 에이전트 하네스(claude code, codex 등)와의 대화로 수행하고, **모든 지식은
이 레포 안에 존재**한다. 인간의 암묵지가 레포 밖에 남으면 안 된다.

- 지식은 "저장 위치"가 아니라 **"포착 시점"**의 문제다. 지식은 큰맘 먹고 쓰는 문서가
  아니라 매 세션에서 흘러나오므로, 포착을 **모든 작업의 강제 부산물**로 만든다.
  → [/decisions/knowledge-capture.md](/decisions/knowledge-capture.md)
- 명시적 예외: **인프라 계정·버킷 설정**은 레포 밖 암묵지로 둔다.
  → [/decisions/infrastructure.md](/decisions/infrastructure.md)

## 2. catalog-in-repo

공간데이터 메타데이터를 **STAC 1.1.0**으로 관리하고, static STAC을 **JSON으로 git에서
직접 버전 관리**한다.

- 데이터에 관한 사실의 SSOT는 STAC. 그 외 지식은 OKF.
  → [/decisions/knowledge-architecture.md](/decisions/knowledge-architecture.md)
- 카탈로그·접근 정책 → [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)

## 3. reproducibility

데이터 **처리 과정**이 완전히 재현 가능해야 한다 — 같은 입력으로 처리 코드를 돌리면
같은 출력이 나와야 한다.

- 재현성은 입력이 고정될 때만 성립한다. 원본·입력·코드 세 층을 모두 pin한다.
  → [/decisions/reproducibility.md](/decisions/reproducibility.md)

## 이 결정들이 검증되는 방식

세 원칙 중 무엇도 "적힌 지식이 참인가"를 스스로 보장하지 못한다. 진위 검증은
**사용자 피드백 루프**(사후)가 담당한다. 포착 메커니즘은 "빠짐없이 적히게"까지만,
"참인가"는 피드백 루프가 책임진다.
→ [/decisions/governance-and-review.md](/decisions/governance-and-review.md)
