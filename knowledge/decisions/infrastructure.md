---
type: decision
title: 인프라 — 팀 소유 R2, 계정·설정은 암묵지 예외
description: R2 버킷은 팀 소유로 두어 인프라 bus factor를 없앤다. 계정 정보와 버킷 설정은 레포 밖 암묵지로 두는 명시적 예외 구역.
tags: [infrastructure, r2, cloudflare, bus-factor, exception]
timestamp: 2026-07-20
---

# 인프라 — 팀 소유 R2, 계정·설정은 암묵지 예외

## 결정

- 오브젝트 스토리지는 **Cloudflare R2**, 버킷은 **팀 소유**(개인 계정 아님). → 담당자가
  떠나도 데이터가 개인에게 묶이지 않는다. 인프라 bus factor 해소.
- **명시적 예외 구역**: 계정 정보(자격증명·루트 접근·결제)와 버킷 설정(수명주기/티어링/CORS
  등)은 **레포 밖 암묵지로 둔다.**
  - 계정 정보는 비밀이므로 git에 넣지 않는다.
  - 버킷 설정은 콘솔 클릭으로 둔다 — 초기 버킷 생성 1회 + 키 발급만 하므로 IaC/문서화
    비용을 들이지 않는다.

## 왜 이것만 예외인가 (명시)

- [/principles.md](/principles.md)는 "모든 지식은 레포 안에"를 요구하고,
  [/decisions/reproducibility.md](/decisions/reproducibility.md)는 재현성·투명성을 요구한다.
  **인프라는 이 두 원칙의 명시적 예외 구역**이다. 나중에 "왜 이것만 예외지?"라는 혼란을
  막기 위해 예외임을 여기 못박는다.
- 검토했으나 채택하지 않음: 비-비밀 포인터 runbook(계정 존재 사실·버킷명·엔드포인트·
  티어링 정책·자격증명 요청처)을 남기는 안. 단순성을 위해 통째로 암묵지 예외로 두기로 결정.

## 감수한 비용

- 후임 담당자는 인프라 접근 경로를 레포에서 찾을 수 없다. 인수인계는 사람 대 사람으로
  이루어져야 한다 ([/decisions/reproducibility.md](/decisions/reproducibility.md)의
  냉동 티어링 정책이 실제 걸려 있는지도 레포로 검증 불가).

## 관련

- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md) — 자격증명 게이트의
  목적·정책
- [/decisions/reproducibility.md](/decisions/reproducibility.md)
