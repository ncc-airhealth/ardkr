---
name: design-stac-metadata
description: 파이프라인 스크립트에서 STAC collection·item 메타데이터 내용을 설계할 때 발동.
---

# design-stac-metadata

파이프라인 스크립트가 기록할 STAC 메타데이터 **내용**을 설계할 때 따르는 규약.

`stac-metadata/` JSON은 파이프라인 스크립트가 생성한다.
손으로 직접 고치지 않는다.
예외는 version extension으로 deprecated 전환하는 경우뿐이다.

PySTAC API는 `../use-pystac/SKILL.md`, 문체는 `../write-korean/SKILL.md`를 따른다.
필드 정의는 아래 reference를 본다.

## 정보 배치

품질 판단에 필요한 정보는 다음 순서로 배치한다.

1. STAC core나 공식 extension 필드
2. 외부 근거는 collection/item `links`
3. `__doc__`의 `## 한계` 섹션 (필드와 link만으로는 담기 어려운 결함·미확인 정보·예외·제한사항만)

## 필드와 extension

- STAC core field만 허용
- STAC extension 사용 시, 해당 field 추가 허용
- 사용할 extension은 [STAC Extensions](https://stac-extensions.github.io/)에서 탐색

## links·license·providers

- 외부 자료는 collection/item `links`로 참조
  - link 객체의 `type` 필드는 IANA media type. PySTAC `MediaType` 상수를 우선 확인
  - `title`은 collection 안에서 unique
  - `rel` 필드는 {`via`, `describedby`, `license`, `related`}를 값으로 허용
- `license` — STAC Collection Spec
- `providers` — STAC Common Metadata (Provider)


## description

- 파이프라인 스크립트에서 collection 정의 시, `description=__doc__`로 넘김
- 대상 독자는 데이터 분석가/연구자
- 엄밀함과 구체성을 유지하고, UI 미리보기용으로 사실을 줄이지 않음
- 맨 위는 제목 없이 데이터 소개와 처리 의도를 2–3문장으로 작성
- 원본이 설명하지 않는 내용은 추정하지 않음
- description 이외의 필드(`라이선스`, `item` 등)에 작성된 내용은 제외
- `## 한계`에는 `../inspect-data-quality/SKILL.md` 조사 결과 중 필드와 link로 담기 어려운 항목만 기록

## reference

- **STAC Collection Spec** — https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md
- **STAC Item Spec** — https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md
- **STAC Extensions README** — https://github.com/radiantearth/stac-spec/blob/master/extensions/README.md
- **STAC Extensions** — https://stac-extensions.github.io/
- **STAC Links** — https://github.com/radiantearth/stac-spec/blob/master/commons/links.md
- **STAC Common Metadata (Provider)** — https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#provider
- **STAC Common Metadata (Date and Time)** — https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#date-and-time
- **IANA link relation 등록표** — https://www.iana.org/assignments/link-relations/link-relations.xhtml
