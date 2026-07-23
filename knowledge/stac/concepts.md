---
type: reference
title: STAC 개념 — Catalog, Collection, Item, Asset, Link, Extension
description: SpatioTemporal Asset Catalog(STAC)의 핵심 객체·관계·extension 메커니즘을 요약한다. 데이터 메타데이터를 구조화할 때 기준이 되는 공통 어휘.
tags: [stac, catalog, collection, item, asset, link, extension, reference]
timestamp: 2026-07-23
---

# STAC 개념

STAC(SpatioTemporal Asset Catalog)은 지구 관측·공간 데이터를 **검색·탐색 가능한 메타데이터**로 기술하는 개방 스펙이다.
핵심은 최소 코어 + 확장(extension)이다.
코어만으로도 Catalog·Collection·Item·Asset을 표현하고, 도메인별 필드는 extension으로 붙인다.

이 문서는 개념만 다룬다.
개별 extension 필드·예시는 [/stac/extensions.md](/stac/extensions.md)를 본다.

## 기반

- 표현은 **JSON**이다.
- Item의 공간 위치는 **GeoJSON Feature**다.
- 필드 제약은 **JSON Schema**로 검증한다.
- 객체 간 관계는 **Link**(RFC 8288 Web Linking)로 표현한다.
- 파일 형식은 IANA media type으로 적는다.
- Collection은 OGC API - Features의 Collection JSON을 확장한 형태다.

`null`과 필드 부재는 같지 않다.
스펙이 `null`의 의미를 정한 필드가 아니면 필드를 넣지 않는다.

## 객체 계층

```text
Catalog (root)
├── Catalog / Collection
│   └── Collection
│       └── Item
│           └── Asset (실제 파일)
│           └── Asset
└── Collection
    └── Item
```

- **Catalog** — 다른 Catalog·Collection·Item으로의 링크만 담는 구조 요소다. 파일 시스템의 폴더에 가깝다.
- **Collection** — Catalog의 필드를 모두 갖고, 여기에 **license**, **extent**(공간·시간), providers, keywords, summaries 등을 더한다. 같은 성격의 Item 묶음의 시작점이다.
- **Item** — 한 시공간 단위의 메타데이터다. GeoJSON Feature이며, 실제 바이트는 Asset 링크로 가리킨다.
- **Asset** — 다운로드·스트리밍할 수 있는 파일 하나다. Item 또는 Collection에 붙는다.
- **Link** — `rel`·`href`·`type` 등으로 부모·자식·관련 자원을 연결한다.

Catalog와 Collection의 역할 구분:

- 사용자가 “데이터셋”으로 찾을 단위 → **Collection**.
- 큰 Collection을 연도·경로 등으로 나누거나, 여러 Collection을 묶는 입구 → **Catalog**.

한 Item은 하나의 Collection에만 속한다.
Item은 보통 자신보다 가까운 Collection을 `collection` 필드로 가리킨다.

## Item

Item은 STAC의 검색 단위다.
GeoJSON Feature에 다음을 더한다.

| 영역 | 역할 |
|------|------|
| `geometry` / `bbox` | 공간 범위. 좌표계는 WGS84 경위도(EPSG:4326 계열) |
| `properties.datetime` 등 | 시간 |
| `assets` | 실제 데이터·미리보기 등 파일 맵 |
| `links` | 부모 Collection, self, 관련 자원 |
| `stac_extensions` | 이 Item이 쓰는 extension 스키마 URL 목록 |
| `collection` | 소속 Collection id |

**Spatiotemporal asset**이란, 어떤 공간·시점에 대한 지구 정보를 담은 파일을 말한다.
위성·항공 영상, SAR, 포인트 클라우드, 데이터 큐브, 파생 산출물 등이 해당한다.
GeoJSON 본문은 그 파일의 인덱스가 아니라, **파일로 가는 메타데이터**다.

벡터 레이어(shapefile, GeoPackage 등)를 Asset으로 두는 것은 스펙 best practice에서 권장하지 않는다.
개념적으로 Item·Asset 모델과 잘 맞지 않기 때문이다.

## Asset

Asset 객체는 최소 `href`를 갖고, 보통 `type`(media type), `roles`, `title`을 함께 둔다.

- `href` — 파일 위치. 절대 URL 또는 상대 경로.
- `roles` — 의미 역할. 예: `data`, `thumbnail`, `metadata`, `overview`.
- extension 필드는 Asset에도 붙을 수 있다. 예: `file:checksum`, `proj:code`.

Collection 수준의 assets와 Item Asset Definition(`item_assets`)으로 “이 Collection의 Item들이 가질 수 있는 asset 형태”를 미리 적을 수도 있다.

## Link

Link 객체 핵심 필드:

| 필드 | 의미 |
|------|------|
| `rel` | 관계 종류. 예: `self`, `root`, `parent`, `child`, `item`, `collection` |
| `href` | 대상 URL 또는 경로 |
| `type` | 대상 media type |
| `title` | 사람이 읽는 제목 |

extension이 추가 `rel` 값을 정의하기도 한다.
예: Versioning의 `successor-version`, Scientific의 `cite-as`, Processing의 `derived_from`.

## Collection 필수에 가까운 메타

Catalog 공통: `id`, `description`, `stac_version`, `links`.

Collection이 더 요구하는 대표 필드:

| 필드 | 의미 |
|------|------|
| `license` | SPDX 식별자, SPDX 표현식, 또는 `other` |
| `extent.spatial.bbox` | 공간 범위 목록 |
| `extent.temporal.interval` | 시간 구간 목록. 열린 끝은 `null` |
| `providers` | 생산·처리·호스팅 주체 목록 |
| `summaries` | 소속 Item 속성 값의 요약. 검색·UI용 |

## Common Metadata

코어 Item/Collection에 공통으로 쓸 수 있는 필드 묶음이 있다.
extension이 아니라 스펙 commons다.

대표 그룹:

- 기본: `title`, `description`, `keywords`, `roles`
- 시각: `datetime`, `created`, `updated`, `start_datetime` / `end_datetime`
- 라이선스·제공자: `license`, `providers`
- 관측 수단: `platform`, `instruments`, `constellation`, `mission`, `gsd`
- 밴드·값: `bands`, `nodata`, `data_type`, `statistics`, `unit`

도메인 전용 필드는 commons에 억지로 넣지 말고 extension을 찾는다.

## Static Catalog vs Dynamic Catalog

- **Static** — JSON 파일을 객체 스토리지·git·웹 서버에 두고 링크로 연결한다. 구현이 단순하다.
- **Dynamic** — API나 서버가 요청 시 JSON을 생성한다. STAC API와 함께 쓰는 경우가 많다.

둘 다 같은 Catalog/Collection/Item 모델을 쓴다.
레이아웃·상대/절대 링크 관행은 stac-spec best practices를 본다.

## Extension 메커니즘

코어는 의도적으로 얇다.
실제 데이터 기술은 거의 항상 extension을 조합한다.

### 등록

객체가 extension을 쓰면 `stac_extensions` 배열에 **그 extension의 JSON Schema URL(버전 포함)** 을 넣는다.

```json
"stac_extensions": [
  "https://stac-extensions.github.io/projection/v2.0.0/schema.json",
  "https://stac-extensions.github.io/file/v2.1.0/schema.json"
]
```

식별자 URL은 보통 각 extension README 상단의 Identifier다.

### 필드 이름

- 대부분 `prefix:field` 형태다. 예: `proj:code`, `file:checksum`, `eo:cloud_cover`.
- 일부 extension은 prefix 없이 코어와 같은 위치에 필드를 둔다. 예: Versioning의 `version`, `deprecated`.

### 적용 범위(scope)

extension마다 Catalog / Collection / Item Properties / Asset / Link / Band 등 **어디에 붙는지**가 다르다.
README의 Scope와 필드 표를 본다.

부모·자식 사이 **자동 상속은 없다**.
Item만 Projection을 쓰면 Collection의 `stac_extensions`에 넣을 필요는 없다.
Collection `summaries`나 `item_assets`에 extension 필드를 요약하면 Collection 쪽에도 등록한다.

### Maturity

커뮤니티 extension은 성숙도 등급을 붙인다.

| 등급 | 의미 |
|------|------|
| Proposal | 아이디어 단계. 파괴적 변경이 흔하다. |
| Pilot | 스키마·예시가 있고 일부 카탈로그가 쓴다. 변경 가능. |
| Candidate | 여러 구현이 뒷받침. 대체로 안정. |
| Stable | 변경은 버전·리뷰를 거친다. 가장 안정. |

등급이 낮아도 유용할 수 있다.
다만 스키마가 바뀔 여지를 알고 쓴다.

### 선택 원칙

새 필드를 만들기 전에 [STAC Extensions 목록](https://stac-extensions.github.io/)에서 같은 의미를 담는 extension이 있는지 본다.
이미 있는 필드를 재사용해야 도구·검색·상호운용성이 맞는다.

핵심 extension 필드 요약: [/stac/extensions.md](/stac/extensions.md).

## 이 저장소와의 관계

이 문서는 STAC 일반 지식이다.
geovars가 static STAC을 git의 `stac-metadata/`에 두는 운영 규칙은 [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)에 있다.
데이터 사실은 STAC JSON에, 그 외 간접 지식은 knowledge/에 둔다는 경계는 [/decisions/knowledge-architecture.md](/decisions/knowledge-architecture.md)에 있다.
구조화 가능한 메타는 extension을 적극 쓰고, 아니면 `description`에 적는다.

## 관련

- [/stac/extensions.md](/stac/extensions.md)
- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)
- [/decisions/knowledge-architecture.md](/decisions/knowledge-architecture.md)
- [/principles.md](/principles.md)

# Citations

1. STAC Overview — https://github.com/radiantearth/stac-spec/blob/master/overview.md
2. STAC Extensions (spec) — https://github.com/radiantearth/stac-spec/blob/master/extensions/README.md
3. STAC Extensions 목록 — https://stac-extensions.github.io/
4. STAC Common Metadata — https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md
5. STAC 1.1.0 / stacspec.org — https://stacspec.org/
