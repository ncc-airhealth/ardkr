---
type: decision
title: 거버넌스와 검증
description: 단일 관리자·교체 주기라 self-review를 수용하되, 처리에 검증을 내장하고 검증 기준은 외부 오라클에 근거한다. 진위는 사용자 피드백 루프가 사후에 검증한다.
tags: [governance, review, validation, feedback-loop, bus-factor]
timestamp: 2026-07-21
---

# 거버넌스와 검증

## 운영 전제

- 대부분 **한 명이 관리**하고, 담당자는 **3~12개월마다 교체**된다.
  - 그래서 독립된 두 번째 사람이 없다.

## 결정

### self-review 수용

- 사람 PR 리뷰를 두되, 관리자가 한 명이면 요청·리뷰·승인이 동일인이라 self-review다.
  - 이를 **명시적으로 수용**한다.
- 독립 검증은 사람이 아니라 **다수의 사용자 피드백**(사후)에서 온다.
  - 단일 관리자가 사전에 못 잡는 오류를, 사용자 다수가 배포 후 잡는다.

### 사용자 피드백 루프 (닫힌 루프)

- v1을 배포하면 사용자가 쓰고 피드백을 준다.
  - 그 피드백으로 정정해 v2를 발행한다.
- 이 루프는 **닫혀야** 검증이다.
  - v2는 미래 사용자만 구하므로, v1 사용자가 알 수 있도록 v1에 `deprecated: true`와 `successor-version: v2`, 정정 사유를 부착한다 ([/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)).
  - 사용자는 레포에서 자기 pin 버전의 상태를 조회해 정정을 발견한다 ([/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)).

### 처리 절차 (검증 내장)

데이터 처리는 반드시 다음 절차로 수행한다:

1. 인간의 collection 추가 요청 정의
2. 에이전트가 처리 스크립트(`pipeline/process/<collection-id>.py`) 작성 (**검증 절차 포함**)
3. 인간이 `pipeline/` 실행기(`pipeline/run.py`)로 실행

처리 스크립트 내부:

1. collection 세부 정의
2. item/asset 단위 로컬 프로세싱
3. **검증 절차 수행**
4. 데이터 업로드 (R2)
5. 레포에 메타데이터 저장 (STAC, `stac-metadata/`), 이때 생성된 git commit과 `image` 버전을 provenance에 기록

STAC 메타데이터 생성·관리에는 **pystac**을 쓴다.
스크립트·환경·실행 세부는 [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md) 참고.

### 검증 기준 (self-grading 방지)

- 검증 기준은 **에이전트가 제안, 사람이 개선·승인**한다.
- 사람의 승인은 감·기억이 아니라 **외부 오라클**에 근거해야 연극이 아니다.
  - 오라클은 **데이터 제공처의 공식 문서**(코드북·명세·속성정의서·.prj)다.
  - 원본과 함께 박제하고, 검증 기준은 그것을 citation으로 참조한다.
- **오라클 우선순위**: 한국 공공데이터는 메타데이터가 틀리거나 코드북이 없어서 담당기관에 직접 문의해야 하는 경우가 많다.
  - 충돌 시 **박제된 담당기관 해명이 공식 코드북보다 우선**하며, 판단 근거는 STAC provenance로 남긴다 ([/decisions/knowledge-architecture.md](/decisions/knowledge-architecture.md)).
  - 코드북이 아예 없는 데이터는 담당기관 문의로 확인하고 그 해명을 1급 오라클로 박제한다.

## 분업 (착각 방지)

- 포착 메커니즘([/decisions/knowledge-capture.md](/decisions/knowledge-capture.md))은 "빠짐없이 적히게"까지만 책임진다.
- "적힌 게 참인가"는 **사용자 피드백 루프**가 책임진다.

## 기각한 대안

- **에이전트 교차검증만으로 독립성 확보**와 **낙관적으로 먼저 쓰고 나중에 정정**을 기각했다.
  - 전자는 리뷰어 신뢰 문제이고, 후자는 정정 전까지 오류가 그대로 남는 문제다.
  - 사용자 피드백 루프와 외부 오라클 조합으로 대체한다.

## 관련

- [/decisions/knowledge-capture.md](/decisions/knowledge-capture.md)
- [/decisions/reproducibility.md](/decisions/reproducibility.md)
