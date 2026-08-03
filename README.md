# ardkr

> 대한민국 공간데이터를 analysis-ready 형태로 제공하는 **STAC 카탈로그**.

한국 공간데이터를 재현 가능하게 가공한 뒤, Open STAC Catalog로 배포하는 프로젝트입니다!

## 해결하려는 문제

공간데이터는 생성, 가공 단계에서 GIS, 원격탐사, DB 등 도메인 지식을 요구하는 만큼 데이터를 다루기 위해 일정 수준의 전문성을 요구합니다. **QGIS를 잠깐 다뤄본 사람이 데이터를 완전히 이해하고 설명할 수 있지 않습니다.**  하지만 공공기관이 배포하는 공간데이터는 형식·좌표계·갱신 주기·문서화 수준이 제각각입니다. 

특정 지역 또는 과거 데이터에 대한 접근도 제약이 있으며 데이터를 이해하기 위해 숨은 정보들이 많습니다. 이러한 정보와 데이터를 얻으려면 담당 기관/공무원과의 소통이 요구되며, 신청 절차 또한 번거롭습니다.

이 프로젝트의 구체적인 목표는 다음과 같습니다.

- **Open STAC** — 메타데이터를 Static [STAC](https://stacspec.org/)으로 배포
- **Explainable Data** - 데이터를 이해/활용하기 위한, 공개 가능한 수준의 모든 정보를 메타데이터에 반영
- **Versioning** — 과거 버전의 collection을 보존
- **Reproducible** — 원본 스냅샷과 고정된 처리 환경으로, 동일 입력/출력 확보

## 카탈로그 둘러보기

- [Catalog](https://raw.githubusercontent.com/ncc-airhealth/ardkr/main/catalog/catalog.json)
- [STAC Browser](https://browser.moregeo.it/external/raw.githubusercontent.com/ncc-airhealth/ardkr/main/catalog/catalog.json)
- 데이터 asset은 비공개 데이터 버킷에 둔다. 접근하려면 자격 증명이 필요하다.

보안 서약이 필요한 자료를 보호하고, 스토리지 비용을 관리하기 위해 데이터 버킷 접근을 제한 중입니다.

## 기여

현재 국립암센터 국제암대학원대학교 김선영 교수님 연구팀에서 해당 프로젝트를 운영하고 있습니다.

문의사항은 hangm0101@ncc.re.kr로 전달 부탁드립니다.

## 라이선스

**미정**
