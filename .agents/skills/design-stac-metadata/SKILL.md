---
name: design-stac-metadata
description: 파이프라인 스크립트에서 collection·item 메타데이터 필드, links, description/__doc__, providers, 라이선스 맥락을 설계할 때 따르는 규약. stac-metadata/ JSON 직접 편집은 deprecated 전환 외 금지.
---

# design-stac-metadata

파이프라인 스크립트가 기록할 STAC 메타데이터 **내용**을 설계할 때 따르는 규약.

`stac-metadata/` JSON은 파이프라인 스크립트가 생성한다.
손으로 직접 고치지 않는다.
예외는 version extension으로 deprecated 전환하는 경우뿐이다.

PySTAC API는 `../use-pystac/SKILL.md`, 스크립트 구조는 `../write-pipeline-script/SKILL.md`, 문체는 `../write-korean/SKILL.md`를 따른다.

## 맥락을 메타데이터에 담는다

데이터를 이해하는 데 필요한 지식은 이 레포 안에 있어야 한다.
읽는 사람이 따로 검색해야 알 수 있는 상태로 남기지 않는다.

## 구조화된 정보

- 구조화된 정보는 STAC 코어 필드 또는 공식 extension에만 적음. 임의 커스텀 필드 금지
- 코어 필드 규칙은 [STAC Spec](https://github.com/radiantearth/stac-spec)을 봄
- 사용할 extension을 찾을 때는 [STAC Extensions](https://stac-extensions.github.io/)를 봄
- extension은 실제로 그 필드를 쓰는 객체에만 선언함. 값 없이 스키마 URI만 얹지 않음

## links

STAC 공통 rel만 쓰고, 관계에 맞지 않으면 억지로 붙이지 않는다.

- `via` — 출처의 비-STAC 메타데이터·원문 페이지
- `license` — 라이선스 원문 문서

## media type

IANA 등록 타입을 쓴다. PySTAC `MediaType` 상수를 우선 확인한다.

## 서술과 `__doc__`

extension으로 담을 수 없는 서술은 모듈 `__doc__`에 둔다.
원본이 설명하지 않는 것은 추정해서 적지 않음. 모른다는 사실을 `__doc__`에 적음.

모듈 `__doc__`이 collection `description`의 단일 출처다.
`description=__doc__`로 넘기고, 설명을 다른 곳에 중복해 쓰지 않는다.
`description`은 마크다운을 허용하므로 `__doc__`도 마크다운으로 쓴다.

**담을 내용**

- 데이터 소개
- 출처와 라이선스 맥락
- 처리 의도
- 한계·주의사항

**담지 않을 내용**

- 코드 절차 설명
- extension으로 표현할 수 있는 구조 정보 (좌표계, checksum, 스키마 등)
