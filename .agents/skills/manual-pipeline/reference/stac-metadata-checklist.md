# STAC metadata checklist

`catalog/<collection-id>/<version>/**.json`의 검토 기준.

## 원칙

- [ ] 조사 결과가 metadata에 반영되어 있다.
- [ ] Collection에는 데이터셋 공통 의미·범위만 둔다.
- [ ] Item에는 개별 시공간 단위와 Item 고유 정보만 둔다.
- [ ] Asset에는 파일의 의미·형식·역할이 드러난다.
- [ ] 생성된 metadata에 placeholder·예시 기본값·임시 범위가 남아 있지 않다.

## Extension 선택

- [ ] [Tabular](https://github.com/stac-extensions/table)
- [ ] [GIS](https://github.com/stac-extensions/projection)
- [ ] [Raster](https://github.com/stac-extensions/raster)
- [ ] [Raster/Reflectance](https://github.com/stac-extensions/eo)

## 필드 구성

- [ ] metadata는 STAC core field와 공식 STAC extension으로 구성한다.
- [ ] 사용한 extension은 적용 범위·필드 의미에 맞게 쓴다.
- [ ] 사용한 extension의 공식 schema URL·버전이 `stac_extensions`에 있다.
- [ ] [STAC Extensions](https://github.com/stac-extensions/stac-extensions.github.io/blob/main/README.md)에 등재된 extension만 사용한다.
- [ ] 적절한 extension이 없다면 `description`에 기록한다.

## 필드 정의

- [ ] `stac_version`이 `"1.1.0"`이다.
- [ ] `id`, `version`, `license`가 정의되어 있다.
- [ ] `description`은 한국어 Markdown이다.
- [ ] `title`은 한국어를 기본으로 한다. (기관명·플랫폼 등 고유명사 영문 허용)
- [ ] `keywords`는 한국어를 기본으로 한다. (고유명사 영문 허용)
- [ ] `providers`의 name·roles·url이 확인된 주체·역할과 맞다.
- [ ] `providers.roles` 값은 `producer`, `processor`, `licensor`, `host`만 허용한다.
- [ ] `license`는 SPDX 식별자·표현식, `proprietary`, 또는 `various`이다. SPDX 목록 밖이면 `proprietary`를 쓰고 `license` link로 근거를 남긴다.

## Link

- [ ] 출처·대체·라이선스·관련 `rel` 필드의 값이 적절히 사용되었다.
  - `alternate`: 동일 내용의 다른 표현 (예: `text/html` 웹 페이지)
  - `canonical`: 정본(canonical) 위치
  - `via`: 원본 메타데이터·데이터 서비스 (비-STAC 원천)
  - `license`: 이용 조건
  - `derived_from`: 생성에 쓰인 STAC 엔티티
  - `describedby`: 설명 문서
  - `related`: 관련 자료
- [ ] `type` 필드의 값이 적절히 사용되었다.
  - `application/json`: Catalog/Collection (및 일반 JSON)
  - `application/geo+json`: Item (GeoJSON)
  - `image/tiff; application=geotiff; profile=cloud-optimized`: Cloud Optimized GeoTIFF (COG)
  - `image/png`: PNG (썸네일 등)
  - `image/jpeg`: JPEG (썸네일 등)
  - `application/geopackage+sqlite3`: GeoPackage
  - `application/x-parquet`: Parquet / GeoParquet
  - `text/html`: HTML
  - `application/pdf`: PDF
