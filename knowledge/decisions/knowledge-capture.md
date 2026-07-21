---
type: decision
title: 지식 포착 — continuous, boundary-triggered
description: 암묵지 포착은 회고가 아니라 모든 작업의 강제 부산물. 신뢰할 수 있는 경계(작업완료/상시지침) 2층에 트리거를 건다 — CI 기반 게이트는 CI 미도입 결정으로 제거.
tags: [agent-native, knowledge-capture, okf, handoff, ci]
timestamp: 2026-07-21
---

# 지식 포착 — continuous, boundary-triggered

## 문제

- 담당자가 3~12개월마다 교체된다. 매 교체마다 공무원/기관 연락 이력, "이 기관 데이터는
  의심하라" 같은 휴리스틱, 진행 중 맥락이 증발할 위기를 맞는다.
- "OKF에 담는다"는 **장소**이지 **포착**이 아니다. 실패는 장소가 없어서가 아니라 **지식이
  생겨나는 순간에 안 적히기** 때문이다. "떠날 때 뇌를 덤프하라"는 회고식 인수인계는 매번
  실패한다.

## 결정: 포착은 continuous (모든 작업의 강제 부산물)

작업을 에이전트 없이 하지 않으므로, 매 세션이 곧 포착 기회다. 포착을 회고 과제가 아니라
**모든 작업의 부산물**로 만든다. 단, "적절한 순간에 skill 트리거"는 **순간 인식에 의존**해
약하므로, 트리거를 **신뢰할 수 있는 경계**에 건다. 두 층을 둔다 (2026-07-21: CI를
도입하지 않기로 확정하면서 CI 기반 "PR 냄새 게이트" 층은 제거했다 —
[/decisions/reproducibility.md](/decisions/reproducibility.md)):

1. **작업 완료 경계 (주력)** — 처리 절차의 **건너뛸 수 없는 마지막 단계**로 "이번에 새로
   생긴 durable 지식을 STAC/OKF에 반영"을 박는다. skill을 "부르는" 게 아니라 workflow
   정의에 완료 조건으로 포함시켜, 없으면 작업이 **미완료**.
2. **상시 행동 지침** — `CLAUDE.md`에 "대화 중 durable 지식이 나오면 **즉시 제안**하고
   사람이 확인"을 에이전트 기본 행동으로 박는다. 1번이 놓치는 대화 중간의 깨달음을 잡는다.
   (이 레포는 **Claude 전용**으로 운영한다 — 팀이 Claude 구독 플랜을 지원하고, 포착
   메커니즘도 Claude Code skill에 의존하기 때문이다.)

### CI 안전망 제거의 트레이드오프

- "데이터/STAC/processing은 바뀌었는데 지식은 한 줄도 안 바뀐" 누락을 사람·에이전트
  판단 없이 자동으로 잡아주던 유일한 장치가 사라졌다. 이제 이 누락은 **전적으로
  1·2번(에이전트 자기규율)에 의존**한다 — 독립적 자동 안전망 없이 운영하기로 의식적으로
  감수한 리스크다.

## 무엇을 남기나 (담당자 교체 생존)

- 기관·부서 **연락망**과 문의 이력 (개인 실명·연락처보다 기관·부서 단위 귀속 기본).
- **불신 휴리스틱** ("A기관 좌표계는 늘 검증", "B데이터는 매년 4월 갱신") — 비난이 아니라
  증거 기반 중립 서술로.
- **진행 중 작업의 맥락** (반쯤 만든 collection, 미해결 피드백).

이 모두 [/principles.md](/principles.md)의 agent-native 원칙(모든 지식은 레포 안에)의 실행.

## 한계 (분업)

- 이 메커니즘 중 무엇도 "적힌 지식이 참인가"는 검증하지 못한다. 진위는
  [/decisions/governance-and-review.md](/decisions/governance-and-review.md)의 사용자
  피드백 루프가 사후에 책임진다.

## 관련

- [/decisions/governance-and-review.md](/decisions/governance-and-review.md)
- [/decisions/knowledge-architecture.md](/decisions/knowledge-architecture.md)
