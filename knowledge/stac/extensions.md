---
type: reference
title: STAC Extension — 핵심 8종 필드 요약과 탐색 소스
description: File Info, Projection, Scientific Citation, Versioning, Processing, Electro-Optical, Classification, Grid extension의 목적·주요 필드·예시를 정리하고, 그 외 extension 탐색 링크를 둔다.
tags: [stac, extension, file, projection, scientific, version, processing, eo, classification, grid, reference]
timestamp: 2026-07-23
---

# STAC Extension

STAC 코어 개념은 [/stac/concepts.md](/stac/concepts.md)를 본다.
이 문서는 **지정한 핵심 extension 8개**의 목적·주요 필드·짧은 예시를 정리한다.
스키마 전문·모든 선택 필드는 각 공식 README·JSON Schema가 권위 있는 기준이다.

## 사용 방법 (공통)

1. 필요한 extension README에서 **Identifier**(JSON Schema URL)를 확인한다.
2. 그 URL을 대상 Catalog / Collection / Item의 `stac_extensions`에 넣는다.
3. Scope에 맞는 위치(Item properties, Asset, Collection summaries 등)에 필드를 적는다.
4. extension이 정의한 `rel` 타입이 있으면 `links`에도 반영한다.

부모·자식 자동 상속은 없다.
필드를 실제로 쓴 객체에 `stac_extensions`를 등록한다.

## 그 외 extension 탐색

이 문서에 없는 extension은 아래를 본다. 92개 전후가 목록에 있다.

| 소스 | 용도 |
|------|------|
| https://stac-extensions.github.io/ | **1순위.** 전체 extension 목록, prefix, maturity, 버전, 한 줄 설명 |
| https://github.com/stac-extensions | 커뮤니티 extension 저장소 모음 |
| https://github.com/radiantearth/stac-spec/blob/master/extensions/README.md | extension 동작·maturity 정의·새 extension 제안 절차 |
| 각 extension README의 Identifier URL | 스키마 버전 고정·검증 |

목록에 없으면 비슷한 의미의 기존 필드를 먼저 찾고, 없을 때만 커스텀 필드 또는 `description`을 검토한다.

## 이 문서가 다루는 extension

| Extension | Prefix | Maturity | Scope (요약) | Schema |
|-----------|--------|----------|--------------|--------|
| File Info | `file` | Stable | Item, Catalog, Collection의 Asset/Link | [v2.1.0](https://stac-extensions.github.io/file/v2.1.0/schema.json) |
| Projection | `proj` | Stable | Collection, Item, Asset | [v2.0.0](https://stac-extensions.github.io/projection/v2.0.0/schema.json) |
| Scientific Citation | `sci` | Stable | Collection, Item | [v1.0.0](https://stac-extensions.github.io/scientific/v1.0.0/schema.json) |
| Versioning Indicators | 없음 | Candidate | Collection, Item 등 | [v1.2.0](https://stac-extensions.github.io/version/v1.2.0/schema.json) |
| Processing | `processing` | Candidate | Item properties/Asset, Collection provider 등 | [v1.2.0](https://stac-extensions.github.io/processing/v1.2.0/schema.json) |
| Electro-Optical | `eo` | Stable | Item properties, Asset, Band | [v2.0.0](https://stac-extensions.github.io/eo/v2.0.0/schema.json) |
| Classification | `classification` | Pilot | Item, Collection, Asset/Band | [v2.0.0](https://stac-extensions.github.io/classification/v2.0.0/schema.json) |
| Grid | `grid` | Pilot | Item | [v1.1.0](https://stac-extensions.github.io/grid/v1.1.0/schema.json) |

---

## File Info (`file`)

**목적:** asset·link 파일의 크기·체크섬·바이트 순서 등 파일 자체의 속성을 적는다.
바이트 진위 검증·캐시·다운로드 UX에 쓰인다.

**주요 필드 (Asset / Link)**

| 필드 | 타입 | 의미 |
|------|------|------|
| `file:checksum` | string | Multihash. 소문자 hex. 알고리즘이 해시 자체에 인코딩된다 |
| `file:size` | integer | 바이트 크기. 상한 없는 정수. 큰 파일은 언어별 big int 주의 |
| `file:header_size` | integer | 헤더 크기(바이트) |
| `file:byte_order` | string | `big-endian` 또는 `little-endian` |
| `file:local_path` | string | 내려받았을 때 상대 로컬 경로 힌트 |
| `file:values` | array | **deprecated.** 값→의미 매핑. Classification extension을 쓴다 |

**체크섬 예 (내용 ASCII `test`의 SHA2-256 multihash)**

```text
12209f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
```

**예시**

```json
{
  "href": "s3://bucket/path/data.parquet",
  "type": "application/vnd.apache.parquet",
  "roles": ["data"],
  "file:size": 1048576,
  "file:checksum": "1220aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

**공식:** https://github.com/stac-extensions/file

---

## Projection (`proj`)

**목적:** asset이 쓰인 **좌표계(CRS)** 와, 가능하면 원본 격자·변환 정보를 적는다.
코어 Item의 `geometry`/`bbox`는 경위도(WGS84)다.
원본 투영 좌표·픽셀 격자 정보는 이 extension에 둔다.

Item properties에 두면 그 Item의 asset 공통 기본값이다.
썸네일만 다른 CRS면 해당 Asset에 필드를 덮어쓴다.

**주요 필드**

| 필드 | 타입 | 의미 |
|------|------|------|
| `proj:code` | string\|null | 권위+코드. 예: `EPSG:5186`, `EPSG:4326` |
| `proj:wkt2` | string\|null | WKT2 CRS 문자열 |
| `proj:projjson` | object\|null | PROJJSON CRS 객체 |
| `proj:geometry` | GeoJSON geometry | **asset CRS**에서의 footprint. 경위도가 아닐 수 있다 |
| `proj:bbox` | [number] | asset CRS bbox. 2D면 4개, 3D면 6개 |
| `proj:centroid` | object | `{ "lat", "lon" }` 경위도 중심 |
| `proj:shape` | [integer] | 기본 격자 픽셀 수 `[height, width]` 즉 Y, X |
| `proj:transform` | [number] | 기본 격자 affine 계수 |

최소 한 필드는 있어야 한다.
가능하면 CRS 설명 + 격자 정보를 같이 둔다.

**주의**

- v2에서 `proj:epsg`는 제거됐다. `"proj:epsg": 32659` → `"proj:code": "EPSG:32659"`.
- 레지스트리에 없는 CRS는 `proj:wkt2` 또는 `proj:projjson`을 쓴다.
- 위치 없는 썸네일은 `proj:code: null`과 `proj:shape` 조합을 권장한다.

**GDAL 등이 파일을 안 열고도 격자를 쓰려면** CRS 하나(`code`/`wkt2`/`projjson`)와 다음 중 하나:

- `proj:transform` + `proj:shape`
- `proj:transform` + `proj:bbox`
- `proj:bbox` + `proj:shape`

**예시**

```json
{
  "proj:code": "EPSG:5186",
  "proj:shape": [1000, 1000],
  "proj:transform": [1.0, 0.0, 200000.0, 0.0, -1.0, 500000.0]
}
```

**공식:** https://github.com/stac-extensions/projection

---

## Scientific Citation (`sci`)

**목적:** 데이터의 DOI·인용 문장·관련 출판물을 적는다.
재현·인용·출처 추적용이다.

**주요 필드 (Item properties / Collection)**

| 필드 | 타입 | 의미 |
|------|------|------|
| `sci:doi` | string | 데이터 DOI 이름만. URL이 아니다. 예: `10.1000/xyz123` |
| `sci:citation` | string | 사람이 쓸 권장 인용 문자열. 스타일은 자유, 식별에 필요한 정보는 포함 |
| `sci:publications` | [Publication] | 관련 출판물 목록 |

**Publication 객체**

| 필드 | 타입 | 의미 |
|------|------|------|
| `doi` | string | 출판물 DOI 이름 |
| `citation` | string | 출판물 인용 문자열 |

**링크**

- `sci:doi`가 있으면 `links`에 `rel: cite-as`인 DOI 링크를 두는 것이 좋다. RFC 8574.

**예시**

```json
{
  "sci:doi": "10.5281/zenodo.1234567",
  "sci:citation": "Hong, S. (2024). Example Dataset. Zenodo.",
  "sci:publications": [
    {
      "doi": "10.1000/journal.2024.001",
      "citation": "Hong, S. et al. (2024). Paper title. Journal."
    }
  ]
}
```

여러 출판물을 한 테이블 Item이 아우를 때는 단수 `sci:doi`보다 `sci:publications`가 맞는 경우가 많다.

**공식:** https://github.com/stac-extensions/scientific

---

## Versioning Indicators

**목적:** 자원의 버전 문자열, deprecated/experimental 표시, 버전 간 링크를 둔다.
prefix가 없다. 필드 이름이 `version`, `deprecated` 등 그대로다.

**주요 필드**

| 필드 | 타입 | 의미 |
|------|------|------|
| `version` | string | 이 자원의 버전 |
| `deprecated` | boolean | 더 이상 쓰지 말 것. 기본 `false`. `latest-version` 링크를 권장 |
| `experimental` | boolean | 불안정·변경 가능. 기본 `false` |

**링크 `rel`**

| rel | 의미 |
|-----|------|
| `latest-version` | 최신 버전 자원. 자원당 최대 1개 |
| `predecessor-version` | 직전·이전 버전. 여러 개 가능 |
| `successor-version` | 다음 버전. 여러 개 가능 |
| `version-history` | 변경 이력·changelog 또는 버전 목록 Catalog/Collection |

**예시**

```json
{
  "version": "0.1.0",
  "deprecated": false,
  "experimental": true,
  "links": [
    {
      "rel": "successor-version",
      "href": "../version=0.2.0/collection.json",
      "type": "application/json"
    }
  ]
}
```

Processing extension의 `processing:version`·`processing:software`와 역할이 다르다.
이쪽 `version`은 **메타데이터/자원 버전**에 가깝다.

**공식:** https://github.com/stac-extensions/version

---

## Processing (`processing`)

**목적:** 어떤 처리 사슬·수준·소프트웨어로 데이터가 만들어졌는지 적는다.
추적성·처리 레벨 검색·알고리즘 버전 구분에 쓰인다.
Collection 전체에 공통이면 Collection 쪽에 두는 것을 권장한다.

**주요 필드**

| 필드 | 타입 | 의미 |
|------|------|------|
| `processing:level` | string | 처리 수준 짧은 이름. `Level`이 아니라 `L1`, `L2`처럼 `L` 형태 |
| `processing:lineage` | string | 처리·모델 경위를 설명하는 자유 텍스트 |
| `processing:facility` | string | 생산 시설·조직 이름 |
| `processing:datetime` | string | 처리 시각 UTC, RFC 3339 |
| `processing:version` | string | 주 처리 체인·baseline 버전. 검색 필터용으로 쓰기 좋음 |
| `processing:software` | object | `{ "패키지명": "버전" }` 맵. 재현용. 태그나 커밋 해시 가능 |
| `processing:expression` | object | 처리 식/체인. `format` + `expression` |

**권장 처리 수준 예:** `RAW`, `L0`, `L1`, `L2`, `L3`, `L4`.
제품 고유 수준 이름을 써도 된다.

**버전 필드 구분**

| 필드 | 용도 |
|------|------|
| `processing:version` | 사용자가 필터할 단일 처리 버전 |
| `processing:software` | 라이브러리·도구 목록. 정보·재현 |
| `version` (Versioning) | 메타데이터/카탈로그 자원 버전 |

**링크 `rel` 예**

| rel | 의미 |
|-----|------|
| `derived_from` | 입력으로 쓴 STAC Item 등 |
| `processing-expression` | 처리 체인·스크립트 |
| `processing-software` | lock 파일 등 소프트웨어 명세 |
| `processing-execution` | 실행 기록. 예: OGC Process API |
| `processing-validation` | 처리 후 검증 보고서·스크립트 |

**적용 위치 요약**

- Item: 주로 `properties`. Asset에도 가능. 필드 최소 1개.
- Collection: 주로 `providers` 중 `producer`/`processor` 역할. summaries·assets에도 가능.

**예시**

```json
{
  "processing:level": "L2",
  "processing:version": "1.0.0",
  "processing:software": {
    "geopandas": "1.0.1",
    "pyproj": "3.6.1"
  },
  "processing:datetime": "2026-07-21T12:00:00Z"
}
```

**공식:** https://github.com/stac-extensions/processing

---

## Electro-Optical (`eo`)

**목적:** 단일 시점 지구 스냅샷 형태의 **전자광학** 관측을 기술한다.
가시·근적외·열적외 등 분광 밴드, 운량·설빙 피복 추정 등.

플랫폼·센서 이름은 commons의 Instrument 필드(`platform`, `instruments` 등)를 같이 쓰는 것이 좋다.
관측 기하(시야각 등)는 View extension을 권장한다.

**주요 필드**

| 필드 | 타입 | 위치 | 의미 |
|------|------|------|------|
| `eo:cloud_cover` | number | Item/Asset | 운량 추정 %. 0–100 |
| `eo:snow_cover` | number | Item/Asset | 설빙 피복 추정 %. 0–100 |
| `eo:common_name` | string | Band | 밴드 통용 이름. 예: `blue`, `green`, `red`, `nir`, `swir16` |
| `eo:center_wavelength` | number | Band | 중심 파장 μm |
| `eo:full_width_half_max` | number | Band | FWHM μm |
| `eo:solar_illumination` | number | Band | 태양 조도 W/m²/μm |

최소 한 필드는 있어야 한다.
`eo:common_name` 허용 목록은 README의 common band names 표가 권위 있는 기준이다.

**예시**

```json
{
  "eo:cloud_cover": 12.5,
  "bands": [
    {
      "name": "B04",
      "eo:common_name": "red",
      "eo:center_wavelength": 0.665,
      "eo:full_width_half_max": 0.03
    },
    {
      "name": "B08",
      "eo:common_name": "nir",
      "eo:center_wavelength": 0.842,
      "eo:full_width_half_max": 0.115
    }
  ]
}
```

**공식:** https://github.com/stac-extensions/eo

---

## Classification (`classification`)

**목적:** 래스터·밴드·모델 출력에 있는 **범주 코드의 의미**를 적는다.
보안 등급(classification)과 무관하다. 픽셀 값의 의미 분류다.

`file:values`를 대체한다. 값 맵이 필요하면 이쪽을 쓴다.

**주요 필드**

| 필드 | 타입 | 의미 |
|------|------|------|
| `classification:classes` | [Class] | 정수 코드 → 클래스 |
| `classification:bitfields` | [Bit Field] | 비트 마스크 필드 정의 |

**Class 객체**

| 필드 | 타입 | 의미 |
|------|------|------|
| `value` | integer | **필수.** 클래스 코드 |
| `name` | string | **필수.** 기계용 짧은 이름. 영문·숫자·`-`·`_` |
| `title` | string | 범례용 표시 이름 |
| `description` | string | 설명 |
| `color_hint` | string | 렌더 색. 대문자 RGB hex, `#` 없음. 예: `FF0000` |
| `nodata` | boolean | nodata 클래스 여부. 기본 false |
| `percentage` | number | 해당 클래스 비율 % |
| `count` | integer | 해당 클래스 화소 수 |

**Bit Field 객체:** `offset`, `length`, `classes` 필수. 비트를 오른쪽에서 왼쪽으로 읽는다.

**붙이는 위치**

- 단일 밴드 래스터 Asset
- 다중 밴드는 Raster extension의 밴드 객체 안
- ML 모델 출력 클래스 정의 등

**예시**

```json
{
  "classification:classes": [
    { "value": 0, "name": "clear", "title": "Clear", "color_hint": "00FF00" },
    { "value": 1, "name": "cloud", "title": "Cloud", "color_hint": "FFFFFF" },
    { "value": 2, "name": "shadow", "title": "Cloud shadow", "color_hint": "808080" }
  ]
}
```

**공식:** https://github.com/stac-extensions/classification

---

## Grid (`grid`)

**목적:** 격자로 쪼갠 제품에서 Item이 속한 **격자 칸 식별자**를 통일된 문자열로 적는다.
UI에서 결과 수가 많을 때 격자 단위로 묶거나, 같은 칸의 약간 다른 footprint를 묶을 때 쓴다.

Scope는 **Item**이다.

**필드**

| 필드 | 타입 | 의미 |
|------|------|------|
| `grid:code` | string | **필수.** `{격자계}-{칸코드}` 형태 |

형식 규칙:

- `grid designation` + `-` + `grid square code`
- 칸 코드는 대문자 영숫자, `_`, `-` 권장

**권장 코드 예**

| 제품·격자 | 형식 예 |
|-----------|---------|
| Sentinel-2 MGRS | `MGRS-35NKA` |
| MODIS Sinusoidal | `MSIN-2506` |
| Landsat WRS-2 | README의 WRS-2 절 참고 |
| NAIP DOQQ 등 | README의 해당 절 참고 |

구현체 고유 격자 체계를 쓸 수도 있다.
공개 목록에 맞추면 검색·집계가 맞기 쉽다.

**예시**

```json
{
  "type": "Feature",
  "properties": {
    "datetime": "2024-06-01T00:00:00Z",
    "grid:code": "MGRS-52SCE"
  }
}
```

**공식:** https://github.com/stac-extensions/grid

---

## 관련

- [/stac/concepts.md](/stac/concepts.md)
- [AGENTS.md](../../AGENTS.md) — 구조화 가능하면 extension 우선
- [write-pipeline-script](../../.agents/skills/write-pipeline-script/SKILL.md) — 발행·버전·검증 계약

# Citations

1. STAC Extensions 목록 — https://stac-extensions.github.io/
2. stac-spec Extensions README — https://github.com/radiantearth/stac-spec/blob/master/extensions/README.md
3. File Info — https://github.com/stac-extensions/file (schema v2.1.0)
4. Projection — https://github.com/stac-extensions/projection (schema v2.0.0)
5. Scientific Citation — https://github.com/stac-extensions/scientific (schema v1.0.0)
6. Versioning Indicators — https://github.com/stac-extensions/version (schema v1.2.0)
7. Processing — https://github.com/stac-extensions/processing (schema v1.2.0)
8. Electro-Optical — https://github.com/stac-extensions/eo (schema v2.0.0)
9. Classification — https://github.com/stac-extensions/classification (schema v2.0.0)
10. Grid — https://github.com/stac-extensions/grid (schema v1.1.0)
