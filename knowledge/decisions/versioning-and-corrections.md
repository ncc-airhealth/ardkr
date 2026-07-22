---
type: decision
title: 버전 관리와 정정
description: 해석-규정 필드는 버전 내 불변, 해석을 바꾸는 정정은 새 버전. 버전 식별자는 MAJOR.MINOR.PATCH로 고정. deprecated/successor로 과거 사용자에게 forward-pointer 제공.
tags: [stac, versioning, corrections, deprecation]
timestamp: 2026-07-21
---

# 버전 관리와 정정

## 결정

- 버전 차원은 `stac-metadata/` 아래에 둔다.
  - **버전 식별자는 `MAJOR.MINOR.PATCH`로 고정한다**(예: `0.0.123`, `3.1.0`).
  - 앞자리 0은 금지한다.
  - 각 자리가 무슨 의미인지, 즉 어떤 변경이면 어디를 올리는지는 규정하지 않는다.
  - 유일한 규칙은 새 버전이 사전식으로 이전 버전보다 커야 한다는 것이다.
  - 그러면 버전이 단조 증가해서, 이 성질만으로 "최신" 판정과 정렬을 할 수 있다.
  - 처리 스크립트는 flat 구조로 최신 버전만 담고, 버전 재현은 git commit provenance로 한다([/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)).
  - 기각한 대안은 `YYYY.MM.DD` 병용이다.
  - collection마다 포맷이 섞이면 "최신" 판정이 기계적으로 어려워진다.
- 데이터 파일(asset)은 불변이다.
  - 버전이 바뀌면 덮어쓰지 않고 새 버전을 생성한다.
- 메타데이터 필드는 두 종류로 나뉜다.
  - **해석-규정 필드**(`proj:code`, 컬럼 의미, 결측값 코드 등)는 데이터 바이트를 안 건드려도 데이터의 해석을 바꾼다.
    - 그래서 버전 내에서 불변이다.
    - 오기입 등 정정이 필요하면 반드시 새 버전을 발행한다.
    - 버전은 해석을 고정하는 단위다.
  - **주석 필드**(`description` 등)는 가변적이라 in-place 수정을 허용한다.
    - git history가 "그때 뭐라고 적혀 있었는가"를 보존하므로 감사가 깨지지 않는다.

## Forward-pointer (과거 사용자 보호)

- 실무에서 데이터 위험은 대개 옛 버전이 이미 발행되어 더는 손댈 수 없게 된 뒤에 발견된다.
  - 사고는 흔히 옛 버전에서 비롯된다.
  - 그래서 원칙적으로 불변이어야 할 옛 버전 메타데이터에도 예외적으로 되쓰기를 허용한다.
- 새 버전 발행 시, 옛 버전에 `deprecated: true`, `successor-version` 링크, 정정 사유를 부착한다(STAC Versioning Indicators extension).
- 이 되쓰기는 데이터 해석을 바꾸지 않는 탐색·경고 메타데이터에 한한다.

## 왜

- "바이트를 안 건드린다"와 "재현성을 안 깬다"는 다른 얘기다.
  - `proj:code` 오기를 in-place로 고치면, 같은 불변 데이터를 같은 경로로 읽은 두 사람이 정반대 결과를 얻는다.
  - 그래서 해석 정정은 새 버전으로 격리해야 [/decisions/reproducibility.md](/decisions/reproducibility.md)가 성립한다.
- STAC 자신의 versioning best practice도 새 버전 발행 시 옛 메타데이터에 `deprecated`/`successor` 되쓰기를 정상 운영으로 본다.

## 관련

- [/decisions/knowledge-architecture.md](/decisions/knowledge-architecture.md)
- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md) — 사용자가 자기 버전의 deprecated 상태를 조회하는 경로

# Citations

1. STAC Versioning Indicators extension — https://github.com/stac-extensions/version
