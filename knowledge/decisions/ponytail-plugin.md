---
type: decision
title: Ponytail 플러그인 도입 — 코드 최소주의 하네스 스킬
description: Claude Code 마켓플레이스 플러그인 Ponytail을 프로젝트 스코프(.claude/settings.json)로 도입. pipeline/process/*.py의 flat/self-contained 원칙과 "재사용 우선" 규칙 충돌 가능성은 미해결.
tags: [harness, plugin, ponytail, code-minimalism, claude-code, agent-native]
timestamp: 2026-07-21
---

# Ponytail 플러그인 도입 — 코드 최소주의 하네스 스킬

## 결정

[Ponytail](https://github.com/dietrichgebert/ponytail)(에이전트가 코드를 짜기 전 "꼭
필요한가 → 이미 있는 코드 → 표준 라이브러리 → 플랫폼 네이티브 → 이미 설치된 의존성 →
한 줄 → 그 다음에만 최소 코드" 우선순위를 강제하는 Claude Code 플러그인)을 **프로젝트
스코프**로 도입한다. `.claude/settings.json`에 커밋:

```json
{
  "extraKnownMarketplaces": {
    "ponytail": {
      "source": { "source": "github", "repo": "DietrichGebert/ponytail" }
    }
  },
  "enabledPlugins": {
    "ponytail@ponytail": true
  }
}
```

(`enabledPlugins`는 배열이 아니라 `"plugin-id@marketplace-id": true` 형태의 객체다 — 최초
작성 시 배열로 잘못 넣어 `Settings Error`가 났고, 이후 바로잡았다.)

## 근거

- 하네스가 **Claude Code 전용**으로 고정돼 있고([/principles.md](/principles.md)),
  Ponytail도 Claude Code 마켓플레이스 경유 플러그인이라 하네스 원칙과 충돌하지 않는다.
- 파이프라인 아키텍처가 이미 최소주의 방향([/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md):
  geovars 단일 패키지, optional extras 엄격 분리, 코어 지연 임포트)이라 철학이 이질적이지
  않다.
- 검증/리뷰 커맨드(`/ponytail-review`, `/ponytail-audit`)는 CI가 아니라 에이전트가 대화
  중 호출하는 방식이라 "CI 미도입" 결정([/decisions/reproducibility.md](/decisions/reproducibility.md))과
  안 부딪힌다. 다만 이 커맨드는 "코드가 과설계됐나"만 보는 축이고, 데이터 해석 검증은
  여전히 [/decisions/governance-and-review.md](/decisions/governance-and-review.md)의
  외부 오라클·사용자 피드백 루프가 책임진다 — 서로 대체 관계가 아니다.

## 기각한 대안

- **A. 규칙만 발췌해 CLAUDE.md/네이티브 skill로 직접 반영** — 외부 마켓플레이스 의존
  없이 근거를 레포 안에서 완결시킬 수 있어 agent-native 원칙에는 더 깔끔하게 맞았지만,
  검토 후 사용자가 B안을 명시적으로 선택.
- **C. 도입하지 않음** — 검토 후 기각.

## 트레이드오프 — 프로젝트 스코프 ≠ 자동 설치

`.claude/settings.json`에 선언해도 팀원이 이 레포를 처음 열 때 마켓플레이스/플러그인
설치를 **직접 승인**해야 실제로 로드된다(신뢰되지 않은 외부 코드 자동 실행 방지). 즉
"무엇을 설치해야 하는지"는 레포에 고정되어 담당자 교체와 무관하게 동일하지만, "실제로
로드돼 있는지"는 각자의 1회 승인에 의존한다 — agent-native 목표(동일 경험) 중 "합의된
도구 목록"은 달성하지만 "완전 자동 적용"까지는 아니다.

## 미해결

- **pipeline/process/*.py와 "재사용 우선" 규칙의 충돌 가능성.** 파이프라인 아키텍처
  결정은 처리 스크립트를 의도적으로 **자기완결·비-DRY**로 유지하기로 확정했다(기각한
  대안: editable 로컬 참조 — "옛 스크립트가 최신 유틸을 써서 재현성 파괴",
  [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)). Ponytail의
  "이미 있는 코드인가? → 재사용" 규칙을 에이전트가 무비판적으로 적용하면 새 collection
  스크립트 작성 시 옛 스크립트의 유틸을 공유하려는 방향으로 끌릴 위험이 있다. 아직
  `pipeline/process/`용 명시적 예외 규칙은 안 정했다 — 실사용 중 마찰이 관찰되면 예외를
  명문화하고 이 문서를 갱신한다.

## 관련

- [/principles.md](/principles.md)
- [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)
- [/decisions/governance-and-review.md](/decisions/governance-and-review.md)
- [/decisions/knowledge-capture.md](/decisions/knowledge-capture.md)
