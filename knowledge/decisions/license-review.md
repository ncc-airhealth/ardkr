---
type: decision
title: collection 추가 시 라이선스 검토 필수
description: 새 STAC collection을 등록하기 전에 원본 데이터의 라이선스·이용 약관을 확인해야 하며, 확인 없이 임시값으로 등록하지 않는다.
tags: [license, stac, collection, governance]
timestamp: 2026-07-23
---

# collection 추가 시 라이선스 검토 필수

## 결정

- 새 collection을 STAC에 등록하기 전에 원본 데이터의 라이선스·이용 약관을 확인한다.
  - 재배포 가능 여부, 출처 표시 의무, 상업적 이용 제한을 확인 대상으로 한다.
  - 확인 결과는 collection의 `license` 필드에 반영하고, 제약이 있으면 STAC `description`에도 적는다.
- 라이선스 확인이 끝나지 않았으면 등록을 보류한다.
  - `"proprietary"` 같은 임시값을 넣는 것은 확인을 생략해도 된다는 뜻이 아니다.
  - `geovars-references`([/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md))는 레포 전체 라이선스 정책이 아직 없어 임시값을 썼다. 그 미해결은 레포 전체 정책 문제이고, 이 문서의 규칙은 collection 하나하나를 등록할 때 개별로 확인하라는 절차 규칙이라 별개다.
- 재배포 불가 라이선스인 원본은 복제하지 않고 checksum과 출처, 취득일만 기록한다.
  - 이미 확정된 규칙([/decisions/reproducibility.md](/decisions/reproducibility.md))을 collection 추가 절차에도 그대로 적용한다.

## 관련

- [/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md)
- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)
- [/decisions/reproducibility.md](/decisions/reproducibility.md)
