---
type: decision
title: 카탈로그와 접근
description: static STAC을 JSON으로 git 커밋, stac-browser로 탐색. 카탈로그는 최신-only, 레포는 전-버전. 카탈로그 public, 데이터는 자격증명 게이트.
tags: [stac, catalog, static-stac, access, r2, stac-browser]
timestamp: 2026-07-21
---

# 카탈로그와 접근

## static STAC (JSON, git 관리)

- 메타데이터는 **JSON으로 직접 작성해 git의 `stac-metadata/`에 커밋**한다 (YAML + pystac
  재생성 방식에서 의식적으로 전환). 커밋된 JSON이 diff·PR 리뷰 대상이 되어 원칙 1·2와 정합.
  버전 차원은 `stac-metadata/`에 산다.
- 외부 STAC 도구가 **URL만으로 크롤**할 수 있게 한다: raw.githubusercontent로 서빙,
  **stac-browser**로 탐색.
- asset `href`는 **R2 절대경로(key)를 그대로** 저장해 데이터 위치를 self-describing하게
  한다 (버킷명/엔드포인트만 별도 env). 카탈로그가 public이어도 asset(R2)은 자격증명
  게이트라, un-credentialed 탐색은 메타데이터까지만 도달한다.

## 카탈로그 구조 vs 레포

- **루트 catalog (정문 · discovery)** — collection당 **최신 버전만 child**. 사용자가 기본적으로
  낡은 데이터를 안 쓰게 한다.
- **레포 (감사 · 재현)** — 과거 메타데이터 **전부 보관**. 옛 버전은 카탈로그 child가
  아니어도 **버전 pin으로 항상 resolve** 가능. "최신 정보는 레포를 참조."
- 이 분리로, v1을 쓴 사용자가 레포에서 v1의 `deprecated`+`successor` 상태를 조회해
  "다시 해야 한다"를 알 수 있다
  ([/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)).

## 카탈로그 유지 절차 (pystac load-mutate-save)

1. 레포에서 catalog를 pystac으로 관리.
2. pystac이 파일 기반으로 catalog를 읽어 상대경로 해석·로딩.
3. Catalog 객체에서 child 수정.
4. Catalog 객체를 파일로 저장.

- **감수한 비용**: 이건 증분 변형이라, collection 파일과 catalog.json이 어긋나도 자동으로
  잡는 대조 장치가 없다 (rebuild-from-scan + CI 검증 대안은 검토 후 **기각** — 단순성 우선).
  드리프트는 사람/에이전트가 절차를 지키는 것에 의존한다.
- **Item JSON**: collection당 item은 보통 20개 미만, 가끔 1000~2000개. 대량 item은 손으로
  쓰지 않고 **처리 스크립트(`pipeline/process/<collection-id>.py`)가 생성**해 `stac-metadata/`에
  커밋한다 ([/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)).

## 사용자와 접근

- 사용자 = **같은 연구팀 내부**. 뼈대가 잡히고 데이터가 채워지면 레포를 **public 전환**.
- **카탈로그(메타데이터)는 public 접근**, **데이터(R2)는 자격증명 게이트**. 레포는 투명하게
  운영하되 데이터 접근만 제약.
- 게이트 목적은 **(A) 책임성·접근관리 + 보안서약 데이터 유출 방지**, **(B) R2 API 요청(Class
  A/B) 비용 통제**(parquet partial read가 다수 요청을 유발). — 둘 다 해당.

## 기밀 처리 (경량)

- 대부분 공공데이터라 메타데이터까지 민감한 경우는 드물다. 예외적으로 메타데이터조차
  민감하면, STAC엔 **최소 정보만** 기록하고 상세는 **게이트된 asset**(별도 문서)에 두고
  STAC에서 그것을 참조한다.

## 미해결

- geovars 카탈로그 유틸 API 세부 (extent/temporal 검색 등).
- static STAC 서빙을 raw.githubusercontent로 계속 갈지, 규모가 커지면 GitHub Pages/R2 서빙으로
  옮길지 (rate limit·CDN 성격 고려).

## 관련

- [/decisions/reproducibility.md](/decisions/reproducibility.md)
- [/decisions/infrastructure.md](/decisions/infrastructure.md)

# Citations

1. stac-browser — https://github.com/radiantearth/stac-browser
