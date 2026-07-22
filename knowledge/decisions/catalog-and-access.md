---
type: decision
title: 카탈로그와 접근
description: static STAC을 JSON으로 git 커밋, stac-browser로 탐색. 카탈로그는 최신 버전만, 레포는 전-버전. 카탈로그 public, 데이터는 자격증명 게이트.
tags: [stac, catalog, static-stac, access, r2, stac-browser]
timestamp: 2026-07-21
---

# 카탈로그와 접근

## static STAC (JSON, git 관리)

- 메타데이터는 **JSON으로 직접 작성해 git의 `stac-metadata/`에 커밋**한다.
  - 커밋된 JSON이 diff·PR 리뷰 대상이 되어 원칙 1·2와 정합한다.
  - 버전 차원은 `stac-metadata/`에 둔다.
- 외부 STAC 도구가 **URL만으로 크롤링**할 수 있도록 raw.githubusercontent로 서빙하고, **stac-browser**로 탐색한다.
- asset `href`는 **R2 절대경로인 key를 그대로** 저장해 데이터 위치를 그 자체로 알 수 있게 한다.
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

- **`SELF_CONTAINED`, 즉 상대경로만 쓰는 방식을 택하고 `ABSOLUTE_PUBLISHED`는 보류한다.**
  - 서빙 URL이, 예컨대 raw.githubusercontent 경로가 아직 확정되지 않았기 때문이다.
  - `geovars/pyproject.toml`의 repo-url TODO와 같은 이유다.
  - URL이 확정되면 self href를 그 URL로 고정하는 `ABSOLUTE_PUBLISHED` 전환을 재검토한다.
  - 이 전환은 아래 "미해결"에 남겨둔다.
- **한국어 설명은 `ensure_ascii=False`로 재직렬화해야 한다.**
  - pystac 기본 직렬화인 `json.dump`는 `ensure_ascii=True`라 한국어가 `\uXXXX`로 이스케이프된다.
  - 그러면 커밋된 JSON이 diff·PR 리뷰 대상이 되어야 한다는 원칙이 깨진다.
  - `normalize_and_save` 이후 `json.load`로 다시 읽어 `json.dump(ensure_ascii=False, indent=2)`로 재저장해야 사람이 읽을 수 있는 diff가 된다.
  - Collection·Item JSON을 쓸 때도 같은 재직렬화가 필요하다.
  - geovars.catalog·geovars.pipeline 헬퍼를 구현할 때 이 재직렬화를 기본값으로 넣는 것을 고려한다.

## 카탈로그 구조와 레포

- **루트 catalog는 정문이자 탐색 지점이라 collection당 최신 버전만 child로 둔다.**
  - 사용자가 낡은 데이터를 쓰지 않게 한다.
- **레포는 감사와 재현을 위한 곳이라 과거 메타데이터를 전부 보관한다.**
  - 옛 버전은 카탈로그의 child가 아니어도 버전을 고정하면 언제든 찾아갈 수 있다.
  - 최신 정보는 레포를 참조한다.
- 이 분리 덕분에 v1을 쓴 사용자는 레포에서 v1의 `deprecated` 상태와 `successor` 정보를 조회해 "다시 해야 한다"는 사실을 알 수 있다 ([/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)).
- 첫 실제 collection인 `geovars-references`([/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md))를 구현하며 구체적인 경로 규칙을 정했다.
  - collection은 `stac-metadata/<collection-id>/version=<version>/`에 self-contained로 저장한다.
  - `collection.json`과 `<item-id>/<item-id>.json`으로 구성된다.
  - 버전 디렉터리 이름은 Hive 스타일 `version=<version>`을 쓰고, S3 asset key도 같은 관행을 따른다.
  - 루트 `catalog.json`의 `rel: child` 링크는 그 collection id의 기존 링크를 지우고 새 버전 경로로 교체한다.
  - 과거 버전 디렉터리는 디스크에서 지우지 않는다.
  - 위에서 정한 "루트는 최신만, 레포는 전-버전" 원칙 그대로다.
  - `geovars.catalog.register_collection_version()`으로 구현했다.
  - 같은 함수가 저장된 모든 JSON을 `ensure_ascii=False`로 재직렬화해, 위에서 남겨둔 재직렬화 기본값 TODO를 해소했다.
- **`Collection.normalize_and_save(root_href, ...)`에는 pystac 버그가 있다.**
  - `root_href`의 마지막 경로 조각에 `.`이 있으면, 예컨대 `version=0.1.0`처럼 버전 문자열이 오면, pystac이 그 조각을 파일명과 확장자로 오인해 통째로 잘라낸다.
  - 그러므로 `root_href` 끝에 `/`를 반드시 붙여야 한다.
  - 자세한 내용은 [/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md)의 "발견한 버그"를 참고한다.
- **`pystac.layout.TemplateLayoutStrategy`는 검토 후 기각한다.**
  - 대상 객체가 트리의 root일 때, 즉 우리처럼 collection을 그 자체로 저장할 때(`is_root=True`) 템플릿을 무시하고 `BestPracticesLayoutStrategy`로 폴백함을 테스트로 확인했다.
  - 이를 우회하려면 루트 Catalog에서부터 전체를 매번 `normalize_and_save`해야 하는데, 이는 위에서 정한 증분 등록 원칙, 즉 한 collection 서브트리만 건드리는 원칙과 충돌한다.
  - 그래서 기각한다.
  - 세부 내용은 [/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md)의 "기각한 대안"을 참고한다.

## 카탈로그 유지 절차 (pystac load-mutate-save)

1. 레포에서 catalog를 pystac으로 관리한다.
2. pystac이 파일 기반으로 catalog를 읽어 상대경로를 해석하고 로딩한다.
3. Catalog 객체에서 child를 수정한다.
4. Catalog 객체를 파일로 저장한다.

- **감수한 비용이 있다.**
  - 이는 증분 변형이라, collection 파일과 catalog.json이 어긋나도 자동으로 잡는 대조 장치가 없다.
  - rebuild-from-scan과 CI 검증을 대안으로 검토했으나 단순성을 우선해 기각했다.
  - 이런 어긋남을 막는 것은 사람과 에이전트가 절차를 지키는 데 의존한다.
- **Item JSON은 collection당 보통 20개 미만이고, 가끔 1000~2000개다.**
  - 대량 item은 손으로 쓰지 않고 처리 스크립트인 `pipeline/process/<collection-id>.py`가 생성해 `stac-metadata/`에 커밋한다 ([/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)).

## 사용자와 접근

- 현재 사용자는 같은 연구팀 내부 인원뿐이다.
  - 뼈대가 잡히고 데이터가 채워지면 레포를 public으로 전환한다.
- 카탈로그, 즉 메타데이터는 public으로 접근할 수 있고 데이터인 R2는 자격증명 게이트를 둔다.
  - 레포는 투명하게 운영하되 데이터 접근만 제약한다.
- 게이트를 두는 목적은 두 가지다.
  - 하나는 책임성과 접근관리, 그리고 보안서약이 걸린 데이터의 유출 방지다.
  - 다른 하나는 R2 API 요청, 즉 Class A/B 비용 통제다.
  - parquet 부분 읽기가 다수 요청을 유발하기 때문이다.

## 기밀 처리 (경량)

- 대부분 공공데이터라 메타데이터까지 민감한 경우는 드물다.
  - 예외적으로 메타데이터조차 민감하면 STAC에는 최소 정보만 기록한다.
  - 상세 내용은 자격증명으로 보호된 별도 asset 문서에 두고, STAC은 그것을 참조한다.

## 미해결

- geovars 카탈로그 유틸 API의 세부 사항을 정해야 한다.
  - extent·temporal 검색 등이 그 대상이다.
- static STAC 서빙을 raw.githubusercontent로 계속할지, 규모가 커지면 GitHub Pages나 R2 서빙으로 옮길지 결정해야 한다.
  - rate limit과 CDN 성격을 고려한다.
- `catalog.json`의 `catalog_type`을 서빙 URL이 확정되면 `SELF_CONTAINED`에서 `ABSOLUTE_PUBLISHED`로 바꿀지 결정해야 한다.
  - 위 static STAC 섹션을 참고한다.

## 관련

- [/decisions/reproducibility.md](/decisions/reproducibility.md)
- [/decisions/infrastructure.md](/decisions/infrastructure.md)

# Citations

1. stac-browser — https://github.com/radiantearth/stac-browser
