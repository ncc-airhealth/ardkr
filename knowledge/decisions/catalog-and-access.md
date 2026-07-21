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

## root catalog.json 구현 (2026-07-21)

빈 root 카탈로그를 pystac으로 생성해 `stac-metadata/catalog.json`에 커밋했다.

```python
import pystac

catalog = pystac.Catalog(id="geovars", title="...", description="...")
catalog.normalize_and_save(
    root_href="stac-metadata",
    catalog_type=pystac.CatalogType.SELF_CONTAINED,
)
```

- **`SELF_CONTAINED`(상대경로만)를 택함, `ABSOLUTE_PUBLISHED`는 보류** — 서빙 URL(raw.githubusercontent
  경로 등)이 아직 확정되지 않았다(`geovars/pyproject.toml`의 repo-url TODO와 동일 사유). URL이
  확정되면 `ABSOLUTE_PUBLISHED`(self href를 그 URL로 고정) 전환을 재검토한다 — 미해결로 아래에 남김.
- **한국어 설명은 `ensure_ascii=False`로 재직렬화 필요** — pystac 기본 직렬화(`json.dump`)는
  `ensure_ascii=True`라 한국어가 `\uXXXX`로 이스케이프되어 diff·PR 리뷰가 불가능해진다(원칙
  "커밋된 JSON이 diff·PR 리뷰 대상" 위반). `normalize_and_save` 이후 `json.load` →
  `json.dump(ensure_ascii=False, indent=2)`로 재저장해야 사람이 읽을 수 있는 diff가 된다. Collection/
  Item JSON을 쓸 때도 동일하게 재직렬화할 것 — geovars.catalog/geovars.pipeline 헬퍼 구현 시
  이 재직렬화를 기본값으로 넣는 것을 고려(TODO).

## 카탈로그 구조 vs 레포

- **루트 catalog (정문 · discovery)** — collection당 **최신 버전만 child**. 사용자가 기본적으로
  낡은 데이터를 안 쓰게 한다.
- **레포 (감사 · 재현)** — 과거 메타데이터 **전부 보관**. 옛 버전은 카탈로그 child가
  아니어도 **버전 pin으로 항상 resolve** 가능. "최신 정보는 레포를 참조."
- 이 분리로, v1을 쓴 사용자가 레포에서 v1의 `deprecated`+`successor` 상태를 조회해
  "다시 해야 한다"를 알 수 있다
  ([/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)).

## collection 버전 디렉터리 구현 (2026-07-21)

첫 실제 collection(`geovars-references`,
[/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md))으로
실제 구현하며 정한 구체적 경로 규칙: **`stac-metadata/<collection-id>/version=<version>/`**
(Hive 스타일 `version=<version>` 명명, S3 asset key도 동일 컨벤션)에 collection을
self-contained로 저장(`collection.json` + `<item-id>/<item-id>.json`), 루트
`catalog.json`의 `rel: child` 링크는 그 collection id의 기존 링크를 지우고 새 버전
경로로 교체(과거 버전 디렉터리는 디스크에서 지우지 않음 — "루트는 최신만, 레포는
전-버전" 그대로). `geovars.catalog.register_collection_version()`으로 구현. 같은 함수가
저장된 모든 JSON을 `ensure_ascii=False`로 재직렬화해, 위 "root catalog.json 구현"에
남겨뒀던 TODO(Collection/Item에도 재직렬화 적용)를 해소했다.

- **pystac 버그 주의**: `Collection.normalize_and_save(root_href, ...)`에서
  `root_href`의 마지막 경로 조각에 `.`이 있으면(`version=0.1.0` 같은 버전 문자열) pystac이
  파일명+확장자로 오인해 그 조각을 통째로 잘라버린다 — **`root_href` 끝에 `/`를
  반드시 붙여야** 회피된다. 실제로 처음엔 이 버그로 `geovars-references/0.1.0/`이
  아니라 `geovars-references/`에 파일이 떨어지는 걸 발견하고 고쳤다
  ([/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md)
  "발견한 버그" 참고).
- **`pystac.layout.TemplateLayoutStrategy`는 검토 후 기각** — 대상 객체가 트리의
  root일 때(`is_root=True`, 우리처럼 collection을 그 자체로 저장) 템플릿을 무시하고
  `BestPracticesLayoutStrategy`로 폴백함을 실제 테스트로 확인. 우회하려면 루트
  Catalog에서부터 전체를 매번 `normalize_and_save`해야 하는데, 이는 위 "카탈로그 구조
  vs 레포"의 **증분 등록**(한 collection 서브트리만 건드림) 원칙과 충돌해 기각. 세부:
  [/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md)
  "두 번째 grilling 라운드".

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
- `catalog.json`의 `catalog_type`을 서빙 URL 확정 시 `SELF_CONTAINED` → `ABSOLUTE_PUBLISHED`로
  바꿀지 (위 "root catalog.json 구현" 참고).

## 관련

- [/decisions/reproducibility.md](/decisions/reproducibility.md)
- [/decisions/infrastructure.md](/decisions/infrastructure.md)

# Citations

1. stac-browser — https://github.com/radiantearth/stac-browser
