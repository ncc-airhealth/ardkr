---
type: decision
title: 카탈로그와 접근
description: static STAC을 JSON으로 git 커밋, stac-browser로 탐색. 카탈로그는 최신 버전만, 레포는 전-버전. 카탈로그 public, 데이터는 자격증명 게이트.
tags: [stac, catalog, static-stac, access, r2, stac-browser, asset-key]
timestamp: 2026-07-23
---

# 카탈로그와 접근

## static STAC (JSON, git 관리)

- 메타데이터는 JSON으로 직접 작성해 git의 `stac-metadata/`에 커밋한다.
  - 커밋된 JSON이 diff·PR 리뷰 대상이 되어 원칙 1·2와 정합한다.
  - 버전 차원도 `stac-metadata/`에 둔다.
- 외부 STAC 도구가 URL만으로 크롤링할 수 있도록 raw.githubusercontent로 서빙하고, stac-browser로 탐색한다.
- asset `href`는 R2 절대경로 key를 그대로 저장해 데이터 위치를 그 자체로 알 수 있게 한다.
  - 버킷명과 엔드포인트만 별도 환경변수로 둔다.
  - 카탈로그가 public이어도 asset인 R2는 자격증명 게이트가 있어, 자격증명 없는 탐색은 메타데이터까지만 도달한다.
- 빈 root 카탈로그는 pystac으로 생성해 `stac-metadata/catalog.json`에 커밋한다.

```python
import pystac

catalog = pystac.Catalog(id="geovars", title="...", description="...")
catalog.normalize_and_save(
    root_href="stac-metadata",
    catalog_type=pystac.CatalogType.SELF_CONTAINED,
)
```

- 상대경로만 쓰는 `SELF_CONTAINED`를 택하고 `ABSOLUTE_PUBLISHED`는 보류한다.
  - 서빙 URL, 예컨대 raw.githubusercontent 경로가 아직 확정되지 않았기 때문이다.
  - `geovars/pyproject.toml`의 repo-url TODO와 같은 이유다.
  - URL이 확정된 뒤의 전환 여부는 미해결에 있다.
- 한국어 설명은 `ensure_ascii=False`로 재직렬화해야 한다.
  - pystac 기본 `json.dump`는 `ensure_ascii=True`라 한국어가 `\uXXXX`로 이스케이프되어, 커밋된 JSON을 사람이 diff로 읽지 못한다.
  - `normalize_and_save` 이후 `json.load`로 다시 읽어 `json.dump(ensure_ascii=False, indent=2)`로 재저장한다.
    - Collection·Item JSON도 같다.
  - `geovars.catalog.register_collection()`이 저장된 모든 JSON에 이 재직렬화를 기본으로 적용해 해소했다.

## 카탈로그 구조와 레포

- 루트 catalog는 정문이자 탐색 지점이라 collection당 최신 버전만 child로 둔다.
  - 사용자가 낡은 데이터를 쓰지 않게 한다.
- 레포는 감사와 재현을 위한 곳이라 과거 메타데이터를 전부 보관한다.
  - 최신 정보는 레포를 참조한다.
  - 옛 버전은 카탈로그의 child가 아니어도 버전을 고정하면 찾아갈 수 있다.
- 이 분리 덕분에 v1을 쓴 사용자는 레포에서 v1의 `deprecated` 상태와 `successor`를 조회해 "다시 해야 한다"는 사실을 알 수 있다 ([/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)).
- 경로 규칙은 첫 collection `geovars-references`([/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md))를 구현하며 정했다.
  - collection은 `stac-metadata/<collection-id>/version=<version>/`에 self-contained로 저장하고, `collection.json`과 `<item-id>/<item-id>.json`으로 구성한다.
  - 버전 디렉터리는 Hive 스타일 `version=<version>`을 쓰고, S3 asset key도 같은 관행을 따른다.
  - **item이 여러 개인 collection은 item 단위로 asset 경로(key)를 묶는다** — `<collection-id>/version=<version>/<item-id>/<filename>`. item 하나에 asset이 여러 개(예: 시도/시군구/읍면동 zip 3개) 붙어도 같은 item 디렉터리 밑에 모인다.
    - item이 하나뿐인 collection은 item 세그먼트를 생략해도 된다(`<collection-id>/version=<version>/<filename>` — `geovars-references`).
    - 실사용 예시: `pipeline/process/sgis-adm-boundary.py`(여러 item, item 단위 경로), `pipeline/process/geovars-references.py`(단일 item, item 세그먼트 생략).
  - 루트 `catalog.json`의 `rel: child` 링크는 그 collection id의 기존 링크를 지우고 새 버전 경로로 교체한다.
  - 과거 버전 디렉터리는 디스크에서 지우지 않는다. "루트는 최신만, 레포는 전-버전" 원칙 그대로다.
  - `geovars.catalog.register_collection()`으로 구현했다.
- 등록 전에 원본 데이터의 라이선스를 확인한다. 확인 없이 임시값으로 등록하지 않는다([/decisions/license-review.md](/decisions/license-review.md)).
- `Collection.normalize_and_save(root_href, ...)`에는 pystac 버그가 있다.
  - `root_href` 마지막 조각에 `.`이 있으면, 예컨대 `version=0.1.0`이면 pystac이 파일명과 확장자로 오인해 잘라낸다.
  - 그러므로 `root_href` 끝에 `/`를 반드시 붙인다 ([/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md)의 "발견한 버그").
- `pystac.layout.TemplateLayoutStrategy`는 기각한다.
  - 대상이 트리 root일 때(`is_root=True`) 템플릿을 무시하고 `BestPracticesLayoutStrategy`로 폴백함을 테스트로 확인했다.
  - 우회하려면 매번 루트 Catalog부터 전체를 `normalize_and_save`해야 해서, 한 collection 서브트리만 건드리는 증분 등록 원칙과 충돌한다 ([/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md)의 "기각한 대안").

## 카탈로그 유지 절차 (pystac load-mutate-save)

1. pystac이 파일 기반으로 catalog를 읽어 상대경로를 해석하고 로딩한다.
2. Catalog 객체에서 child를 수정한다.
3. Catalog 객체를 파일로 저장한다.

- 증분 변형이라 collection 파일과 catalog.json이 어긋나도 자동으로 잡는 대조 장치가 없다.
  - rebuild-from-scan과 CI 검증을 검토했으나 단순성을 우선해 기각했다.
  - 어긋남 방지는 사람과 에이전트의 절차 준수에 의존한다.
- Item JSON은 collection당 보통 20개 미만이고 가끔 1000~2000개다.
  - 대량 item은 손으로 쓰지 않고 처리 스크립트 `pipeline/process/<collection-id>.py`가 생성해 `stac-metadata/`에 커밋한다 ([/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)).

## 사용자와 접근

- 현재 사용자는 같은 연구팀 내부 인원뿐이다.
  - 뼈대가 잡히고 데이터가 채워지면 레포를 public으로 전환한다.
- 카탈로그, 즉 메타데이터는 public으로 접근할 수 있고 데이터인 R2는 자격증명 게이트를 둔다.
  - 레포는 투명하게 운영하되 데이터 접근만 제약한다.
- 게이트 목적은 둘이다.
  - 하나는 책임성·접근관리와 보안서약이 걸린 데이터의 유출 방지다.
  - 다른 하나는 R2 API(Class A/B) 비용 통제다.
    - parquet 부분 읽기가 다수 요청을 유발한다.

## 기밀 처리 (경량)

- 대부분 공공데이터라 메타데이터까지 민감한 경우는 드물다.
  - 예외적으로 메타데이터조차 민감하면 STAC에는 최소 정보만 두고, 상세는 자격증명으로 보호된 별도 asset 문서에 두어 STAC이 참조한다.

## 미해결

- geovars 카탈로그 유틸 API 세부, 예컨대 extent·temporal 검색을 정해야 한다.
- static STAC 서빙을 raw.githubusercontent로 계속할지, 규모가 커지면 GitHub Pages나 R2 서빙으로 옮길지 결정해야 한다. rate limit과 CDN 성격을 고려한다.
- 서빙 URL이 확정되면 `catalog.json`의 `catalog_type`을 `SELF_CONTAINED`에서 `ABSOLUTE_PUBLISHED`로 바꿀지 결정해야 한다.

## 관련

- [/decisions/reproducibility.md](/decisions/reproducibility.md)
- [/decisions/infrastructure.md](/decisions/infrastructure.md)
- [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)

# Citations

1. stac-browser — https://github.com/radiantearth/stac-browser
