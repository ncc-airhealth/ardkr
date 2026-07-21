---
type: decision
title: 첫 실제 collection — geovars-references (연구자료 서지)
description: 인프라 전체 경로(duckdb→parquet→S3 업로드→STAC 등록)를 검증하는 동시에 실사용 가치가 있는 첫 collection으로, geovars 프로젝트 관련 연구자료(논문) 서지를 등록. STAC Scientific Citation extension, 하드코딩 데이터 소스, geovars 공용 유틸의 git-commit pin 실사용을 확정.
tags: [stac, collection, scientific-citation, duckdb, parquet, references, bibliography, geovars-pipeline]
timestamp: 2026-07-21
---

# 첫 실제 collection — geovars-references

`pipeline/`의 "인프라"(duckdb 처리, S3 연결, STAC 카탈로그 등록, `geovars` 공용 유틸
git-pin)가 실제로 맞물려 도는지 확인할 겸, 동시에 실사용 가치가 있는 첫 collection으로
geovars 프로젝트 관련 연구자료(논문) 서지를 골랐다.

## 결정

- **범위: "완전한 테스트 용도"** — 임시 스모크테스트(만들고 지움)가 아니라 **영구
  collection**으로 STAC에 정식 등록한다. 카탈로그 등록 경로 자체도 검증 대상.
- **1 collection = `geovars-references`, item은 논문 1편이 아니라 서지 테이블 하나** —
  `pipeline/process/geovars-references.py`가 duckdb로 하드코딩된 서지 데이터를
  parquet 테이블(컬럼: title_ko/title_en/authors/year/venue/volume/issue/pages/doi/url/
  keywords/added_at)로 만들어 item 하나의 asset으로 붙인다. 논문이 늘면 이 테이블에
  행이 느는 것이지 item이 늘지 않는다.
- **STAC Scientific Citation extension**(`sci:publications`, 리스트 필드) 사용 — item이
  "여러 출판물을 아우르는 테이블"이라 단수 `sci:doi`/`sci:citation`이 아니라 복수용
  `sci:publications: [{doi, citation}, ...]`가 맞다. `cite-as` link도 추가.
  (https://github.com/stac-extensions/scientific)
- **서지 데이터는 스크립트에 하드코딩**(파이썬 리스트) — 별도 CSV/YAML 소스 파일 없이.
  논문 추가 시 이 리스트를 고치고 `VERSION`을 올려 재실행.
- **첫 논문**: DOI `10.11108/kagis.2024.27.3.060` — "환경의 건강 영향 연구를 위한
  공간지리정보 데이터 파이프라인" (김원경 외, 한국지리정보학회지 27(3), 2024). geovars
  프로젝트와 주제가 직접 맞닿아 있어 첫 항목으로 적절하다고 판단.
- **license는 `"proprietary"` placeholder** — 레포 전체의 라이선스 정책이 아직 없어
  기본값을 넣었다. 실제 라이선스 정책이 정해지면 정정 필요(미해결로 아래에 남김).
- **spatial extent는 전역 bbox(`[-180,-90,180,90]`), temporal은 생성일부터 열린
  구간** — 서지 데이터는 본질적으로 비공간적이지만 STAC이 extent를 요구해, 비공간
  collection의 흔한 관행(전역 bbox)을 따랐다.
- **`geovars` 공용 유틸을 실제로 git-commit pin해서 소비** — 이전까지 이 메커니즘은
  설계만 있고 실사용된 적이 없었다. 이번에 처음 실제로 검증:
  - 레포에 이미 `origin`(`github.com/ncc-airhealth/geovars`)이 있지만, **아직
    push하지 않은 로컬 커밋도 pin이 가능해야** 개발 반복이 빨라서 GitHub URL 대신
    `git+file:///workspace@<commit>#subdirectory=geovars`(컨테이너 안에서 레포
    전체가 `/workspace`로 보이는 bind mount를 그대로 활용)로 pin했다. 실제 GitHub
    호스팅 pin은 push 시점에 재검증 필요(미해결).
  - 컨테이너 이미지에 **`git`이 없어서 최초 시도가 실패할 뻔함** —
    `pipeline/images/2026.07.21/Dockerfile`에 `git` 패키지 추가(uv가 `git+` 의존성을
    resolve하려면 `git` 실행파일이 필요). 아직 발행 전 draft 이미지라 in-place 수정.
  - `geovars.pipeline.upload_asset()`/`multihash_sha256()`, `geovars.catalog.
    register_collection_version()`을 이번에 처음 구현해 이 스크립트가 소비했다.

## 근거

- 진짜 collection으로 등록해야 카탈로그 등록 경로(pystac load-mutate-save, 버전
  디렉터리, root catalog child link 교체)까지 실제로 태울 수 있다 — 스모크테스트만으론
  이 부분이 검증되지 않는다.
- geovars 프로젝트 자체가 "환경 변수·공간데이터 파이프라인"을 다루므로, 관련
  연구자료 서지가 나중에도 재사용 가치(레포 어니언테이션·related work 정리)가 있다.

## 기각한 대안

- **논문 1편당 item 1개** — 애초 계획(duckdb→parquet 테이블 하나)과 맞지 않고,
  `sci:publications`가 리스트 필드라 테이블 하나에 여러 논문을 담는 쪽이 자연스러움.
- **서지 데이터를 별도 CSV/YAML 파일로 분리** — 사용자가 "파이프라인 코드에는
  하드코딩"을 명시적으로 선호(YAGNI, 논문 수가 적을 때는 파일 분리가 과함).
- **PDF 원문도 asset으로 저장** — 저작권·용량 이슈로 기각, 서지 메타데이터만.

## 두 번째 grilling 라운드 — 사용자 리뷰 반영 (2026-07-21)

첫 구현을 사용자가 리뷰하며 나온 지적을 `/grill-me`로 하나씩 확정:

- **버전 디렉터리 명명을 `version=<version>`(Hive 스타일)로** — `<version>` 단독보다
  self-describing. S3 asset key와 stac-metadata 로컬 경로 양쪽 다 적용
  (`geovars-references/version=0.1.0/...`). `geovars.catalog.register_collection_version()`
  반영.
- **S3 업로드 전 로컬 스테이징을 `.cache/s3/<key 그대로>`로 통일** — 기존엔
  `.cache/pipeline/<collection-id>/`(scratch_dir)에 만들고 업로드했는데, `.cache/s3/`가
  버킷의 로컬 미러(다운로드 read-through + 업로드 전 staging **양방향**)라는 하나의
  개념으로 통일. `geovars.pipeline.s3_cache_path(key)`/`upload_asset(key)`로 구현(기존
  `upload_asset(local_path, key)` 시그니처에서 `local_path` 제거 — 호출자가 처음부터
  `s3_cache_path(key)`에 쓰면 되므로).
- **lock 파일 위치는 그대로 유지(스크립트 옆)** — 처음엔 `pipeline/process.lock/`으로
  분리하자는 제안이 나왔으나, **uv가 스크립트 lock 경로를 전혀 커스터마이즈할 수 없음을
  실제로 확인**(`uv lock --script`/`uv run --script` 모두 `<script>.lock`을 스크립트
  바로 옆에 고정, 관련 플래그·env var 없음, uv 0.10.11에서 재현 확인). `run.py`가 매번
  복사·이동을 대신하는 방법도 검토했으나 복잡도 대비 이득이 낮아 기각. 에디터 File
  Nesting 설정(예: VSCode `explorer.fileNesting.patterns`) 같은 도구 레벨 해법으로
  대체 가능함을 대안으로 남김.
- **`Processor` 클래스를 모든 `pipeline/process/*.py`의 공식 템플릿으로 확정** — 클래스
  변수(`COLLECTION_ID`/`VERSION`/`TITLE`/`DESCRIPTION`/데이터)+인스턴스 메서드(처리
  단계)+`run()`+`if __name__ == "__main__": Processor().run()`. 사유: 향후 스크립트 간
  상태 공유·가독성. 세부 명세는
  [pipeline-architecture](/decisions/pipeline-architecture.md) "Processor 템플릿".
- **PEP723 의존성은 정확한 버전(`==`)으로 고정** — lock 파일이 이미 전이 의존성까지
  고정하므로 정보상 중복이지만(권장 답변은 `>=` 유지였음), 헤더만 봐도 재현 버전을
  즉시 알 수 있는 명시성을 사용자가 우선함. 예: `duckdb==1.5.4`, `python-dotenv==1.2.2`
  (lock에서 실제 resolve된 값 그대로 사용).
- **`pystac.layout.TemplateLayoutStrategy`는 채택 안 함** — 실제 테스트로 확인:
  `normalize_hrefs`가 대상 객체를 트리의 root로 볼 때(`is_root=True`, 우리처럼
  collection을 그 자체로 저장하는 경우) `collection_template`을 무시하고
  `BestPracticesLayoutStrategy`로 폴백한다(item에는 적용되지만 collection엔 안 먹어
  collection·item 경로가 어긋남 — 실제 재현 확인). 우회하려면 루트 Catalog에서부터
  전체를 `normalize_and_save`해야 하는데, 이는 이 프로젝트가 의도적으로 택한 **증분
  등록**(한 collection의 서브트리만 쓰고 다른 collection은 안 건드림,
  [catalog-and-access.md](/decisions/catalog-and-access.md) "카탈로그 유지 절차") 모델과
  정면으로 충돌한다(발행마다 카탈로그 전체 로드+다른 모든 collection 파일 재저장). 커스텀
  `register_collection_version()`을 그대로 유지.

## 세 번째 리뷰 반영 (2026-07-21)

사용자가 코드를 다시 리뷰하며 3개 개선을 제안, 모두 반영:

- **`REFERENCES`(클래스 변수) → `references`(`@property`)** — 클래스 변수는 "collection
  메타데이터"(`COLLECTION_ID`/`VERSION`/`TITLE`/`DESCRIPTION`)만 담고, 실제 데이터 본문은
  프로퍼티 메서드로 분리. 의미상 구분(설정 vs 데이터)이 목적.
- **pystac 공식 extension 클래스 사용** — 직접 `stac_extensions`/`properties`/`extra_fields`를
  손으로 채우던 것을 pystac이 제공하는 타입 안전한 API로 교체:
  - `pystac.extensions.scientific.ScientificExtension.ext(item, add_if_missing=True)
    .publications = [Publication(doi=..., citation=...), ...]` — `sci:publications` 설정과
    `stac_extensions` 등록, **`cite-as` link 자동 추가**까지 한 번에 처리(수동으로 달던
    `cite-as` link 코드 제거 가능해짐).
  - `pystac.extensions.version.VersionExtension.ext(collection, add_if_missing=True)
    .version = "0.1.0"` — 그동안 버전이 디렉터리명·S3 key에만 있고 **STAC 메타데이터
    자체엔 기록되지 않던 gap**을 메꿈. 이 extension은 `deprecated`/`predecessor`/
    `successor` 링크도 지원해, 다음 버전을 낼 때
    [/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)의
    forward-pointer 요구사항도 이 API로 그대로 구현 가능(TODO로 남김).
  - `pystac.extensions.file.FileExtension.ext(asset, add_if_missing=True).checksum = ...`
    — asset이 이미 item에 붙은 뒤(owner가 있어야) 호출해야 함.
- **duckdb → pandas**: `duckdb.connect()`+`CREATE TABLE`+`executemany`+`COPY TO parquet`
  대신 `pd.DataFrame(self.references).to_parquet(out_path)` 한 줄로 축소. 의존성은
  `pandas==3.0.3`+`pyarrow==25.0.0`(parquet 엔진)로 교체, `duckdb` 의존성 제거.
  duckdb는 Docker+pixi 시스템 이미지가 아니라 스크립트 레벨 PEP723 의존성이었으므로,
  이 교체가 "인프라 검증 범위"(S3 업로드·STAC 등록·git-pin·이미지 빌드)를 줄이지
  않는다 — pandas든 duckdb든 같은 방식(uv가 스크립트 의존성으로 설치)으로 취급됨.

## 발견한 버그 (pystac)

`pystac.Collection.normalize_and_save(root_href, ...)`에서 `root_href`의 마지막
경로 조각에 `.`이 있으면(`MAJOR.MINOR.PATCH` 버전 문자열 등) pystac이 이를 파일명+
확장자로 오인해 그 조각을 통째로 잘라버린다(`/a/b/0.1.0` → self href가
`/a/b/collection.json`이 됨, `0.1.0`이 사라짐). **root_href 끝에 `/`를 명시하면
회피된다.** `geovars.catalog.register_collection_version()`에 이미 반영함
(`geovars/geovars/catalog/__init__.py`). 버전 디렉터리를 다루는 코드를 새로 짤 때
반드시 주의.

## 미해결

- license 정책 — 레포/데이터 전체의 라이선스가 정해지면 `"proprietary"` placeholder
  교체 필요.
- `geovars` 패키지를 실제 GitHub 커밋으로 pin(현재는 `git+file:///workspace` 로컬 pin)
  — push 이후 실제로 동작하는지 별도 검증 필요.
- 서지 데이터가 늘어나 CSV/YAML 분리가 아파지면 그때 재검토(YAGNI).

## 관련

- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)
- [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)
- [/decisions/reproducibility.md](/decisions/reproducibility.md)
- [/decisions/secrets-and-s3-client.md](/decisions/secrets-and-s3-client.md)

# Citations

1. STAC Scientific Citation extension — https://github.com/stac-extensions/scientific
2. STAC File Info extension — https://github.com/stac-extensions/file
3. DOI 10.11108/kagis.2024.27.3.060 — https://doi.org/10.11108/kagis.2024.27.3.060
