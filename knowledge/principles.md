---
type: principle
title: 저장소 운영 원칙
description: 이 저장소의 세 가지 운영 원칙: agent-native, catalog-in-repo, reproducibility.
tags: [foundation, agent-native, stac, reproducibility]
timestamp: 2026-07-22
---

# 저장소 운영 원칙

이 저장소는 공간데이터 처리과정과 카탈로그를 관리한다.
모든 하위 결정은 아래 세 원칙을 따른다.

## 1. agent-native

- 모든 작업은 에이전트(Claude Code)와의 대화로 수행한다.
- 모든 지식은 이 저장소 안에 존재해야 하며, 인간의 암묵지가 밖에 남으면 안 된다.
- 보안이 필요한 정보는 예외적으로 저장소 밖 암묵지로 둔다.

## 2. catalog-in-repo

- 공간데이터 메타데이터를 STAC 1.1.0으로 관리한다.
- static STAC을 JSON으로 git에서 직접 관리한다.
- 데이터에 관한 사실은 STAC에 기록하고, 그 외 지식은 knowledge/에 기록한다.

## 3. reproducibility

- 데이터 처리 과정이 완전히 재현 가능해야 한다.
- 환경과 의존성을 이 저장소에서 관리한다.
