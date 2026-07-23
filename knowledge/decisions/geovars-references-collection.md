---
type: decision
title: 첫 실제 collection — geovars-references (연구자료 서지)
description: 인프라 전체 경로(parquet 변환, S3 업로드, STAC 등록)를 검증하는 동시에 실사용 가치가 있는 첫 collection으로, geovars 프로젝트 관련 연구자료(논문) 서지를 등록. STAC Scientific Citation extension, 하드코딩 데이터 소스, geovars 공용 유틸의 git-commit pin 실사용을 확정.
tags: [stac, collection, scientific-citation, pandas, parquet, references, bibliography, geovars-pipeline]
timestamp: 2026-07-21
---

# 첫 실제 collection — geovars-references

pipeline/ 인프라(parquet 변환, S3 업로드, STAC 등록, geovars 공용 유틸 git-pin) 전체 경로를 검증하는 동시에 실사용 가치가 있는 첫 collection으로 geovars 프로젝트 관련 연구자료(논문) 서지를 골랐다.

## 결정

- 범위는 완전한 테스트 용도로 잡는다.
  - 임시 스모크테스트로 만들고 지우는 게 아니라 영구 collection으로 STAC에 정식 등록한다.
  - 카탈로그 등록 경로 자체도 이 collection으로 검증한다.
- 1 collection은 `geovars-references` 하나이고, item은 논문 한 편이 아니라 서지 테이블 하나다.
  - `pipeline/process/geovars-references.py`가 하드코딩된 서지 데이터를 parquet 테이블로 만들어 item 하나의 asset으로 붙인다.
  - 테이블 컬럼은 title_ko/title_en/authors/year/venue/volume/issue/pages/doi/url/keywords/added_at이다.
  - 논문이 늘면 이 테이블의 행이 늘 뿐 item은 늘지 않는다.
- STAC Scientific Citation extension은 pystac의 공식 extension 클래스로 적용한다.
  - `pystac.extensions.scientific.ScientificExtension.ext(item, add_if_missing=True).publications`에 `Publication(doi=..., citation=...)` 리스트를 대입하면 `sci:publications` 설정과 `stac_extensions` 등록, `cite-as` link 추가까지 한 번에 처리된다.
  - item이 여러 출판물을 아우르는 테이블이라 단수 필드인 `sci:doi`/`sci:citation`이 아니라 복수 필드인 `sci:publications`가 맞다.
- 서지 데이터는 별도 CSV/YAML 파일 대신 스크립트 안에 하드코딩한 파이썬 리스트로 둔다.
  - `Processor` 클래스에서는 이 데이터를 `REFERENCES` 클래스 변수가 아니라 `references`라는 `@property`로 노출한다.
  - 클래스 변수는 `COLLECTION_ID`/`VERSION`/`TITLE`/`DESCRIPTION` 같은 collection 메타데이터만 담고, 데이터 본문은 프로퍼티로 분리해 설정과 데이터를 구분한다.
  - 논문을 추가할 때는 이 리스트를 고치고 `VERSION`을 올려 재실행한다.
- 첫 논문은 DOI `10.11108/kagis.2024.27.3.060`, "환경의 건강 영향 연구를 위한 공간지리정보 데이터 파이프라인"(김원경 외, 한국지리정보학회지 27(3), 2024)이다.
  - geovars 프로젝트와 주제가 직접 맞닿아 있어 첫 항목으로 골랐다.
- license는 레포 전체 정책이 아직 없어 `"proprietary"`를 임시값으로 넣는다(미해결 참고).
- spatial extent는 전역 bbox `[-180,-90,180,90]`, temporal은 생성일부터 열린 구간으로 둔다.
  - 서지 데이터는 본질적으로 비공간적이지만 STAC이 extent를 요구하므로, 비공간 collection에서 흔한 관행인 전역 bbox를 따랐다.
- `geovars` 공용 유틸은 git-commit pin으로 가져와 쓴다.
  - 이 메커니즘은 그동안 설계만 있었고 이번에 처음 검증했다.
  - 레포에 이미 `origin`(`github.com/ncc-airhealth/geovars`)이 있지만, 아직 push하지 않은 로컬 커밋도 pin할 수 있어야 개발 반복이 빨라지므로 GitHub URL 대신 `git+file:///workspace@<commit>#subdirectory=geovars`로 pin한다.
  - 컨테이너 안에서 레포 전체가 `/workspace`로 보이는 bind mount를 그대로 활용한 방식이다.
  - 실제 GitHub 호스팅 pin은 push 이후 별도로 재검증해야 한다(미해결 참고).
- uv가 `git+` 의존성을 resolve하려면 `git` 실행파일이 필요하므로 `pipeline/images/2026.07.21/Dockerfile`에 `git` 패키지를 추가했다.
- `geovars.pipeline.upload_asset()`/`multihash_sha256()`, `geovars.catalog.register_collection()`을 이번에 처음 구현했고, 이 스크립트에서 처음 가져와 쓴다.
- 버전 디렉터리 이름은 `<version>` 단독이 아니라 `version=<version>` 형태의 Hive 스타일로 짓는다.
  - 이름만 보고 버전을 알 수 있는 쪽이 낫기 때문이다.
  - S3 asset key와 stac-metadata 로컬 경로 양쪽에 동일하게 적용한다(`geovars-references/version=0.1.0/...`).
  - `geovars.catalog.register_collection()`에 반영되어 있다.
- S3 업로드 전 로컬 준비 경로는 `.cache/s3/<key 그대로>`로 통일한다.
  - `.cache/s3/`를 버킷의 로컬 미러로 두고, 다운로드 read-through와 업로드 전 준비 단계 양쪽에 같은 개념을 쓴다.
  - 처음엔 `geovars.pipeline.s3_cache_path(key)`와 `upload_asset(key)`로 직접 구현했으나, cloudpathlib 도입([/decisions/cloudpathlib-cache-pattern.md](/decisions/cloudpathlib-cache-pattern.md))으로 `s3_path(key)`/`publish_asset(...)`가 이를 대체했다.
- lock 파일 위치는 스크립트 옆에 그대로 둔다.
  - `pipeline/process.lock/`으로 분리하는 안도 검토했지만, uv가 스크립트의 lock 경로를 바꿀 방법을 전혀 제공하지 않는다.
  - `uv lock --script`와 `uv run --script` 모두 `<script>.lock`을 스크립트 바로 옆에 고정하고 관련 플래그나 환경 변수가 없다는 사실을 uv 0.10.11에서 확인했다.
  - `run.py`가 매번 복사·이동을 대신하는 방법도 검토했지만 복잡도 대비 이득이 낮아 기각했다.
  - 에디터의 File Nesting 설정(예: VSCode `explorer.fileNesting.patterns`) 같은 도구 레벨 해법으로 대체할 수 있다.
- `Processor` 클래스를 `pipeline/process/*.py` 전체의 공식 템플릿으로 확정한다.
  - 인스턴스 메서드(처리 단계)와 `run()`, `if __name__ == "__main__": Processor().run()`으로 구성한다.
  - 스크립트 간 상태 공유와 가독성을 위한 구조다.
  - 정확한 템플릿(모듈 상수 배치 등 세부는 이후 `.claude/skills/write-pipeline-script/SKILL.md`에서 갱신됨)은 그 스킬을 참고한다.
- PEP723 의존성은 `>=` 대신 정확한 버전(`==`)으로 고정한다.
  - lock 파일이 이미 전이 의존성까지 고정하므로 정보상 중복이지만, 헤더만 봐도 재현 버전을 바로 알 수 있는 명시성을 우선했다.
  - `duckdb==1.5.4`, `python-dotenv==1.2.2`처럼 lock에서 resolve된 값을 그대로 쓴다.
- duckdb 대신 pandas를 쓴다.
  - `duckdb.connect()`+`CREATE TABLE`+`executemany`+`COPY TO parquet` 대신 `pd.DataFrame(self.references).to_parquet(out_path)` 한 줄로 줄인다.
  - 의존성은 `pandas==3.0.3`과 `pyarrow==25.0.0`(parquet 엔진)으로 교체하고 `duckdb` 의존성은 제거한다.
  - duckdb는 Docker+pixi 시스템 이미지가 아니라 스크립트 레벨 PEP723 의존성이었으므로, 이 교체가 인프라 검증 범위(S3 업로드·STAC 등록·git-pin·이미지 빌드)를 줄이지 않는다.
  - pandas든 duckdb든 uv가 스크립트 의존성으로 설치하는 방식은 같다.
- `pystac.extensions.version.VersionExtension.ext(collection, add_if_missing=True).version = "0.1.0"`으로 collection에 버전을 기록한다.
  - 그동안 버전이 디렉터리명과 S3 key에만 있고 STAC 메타데이터 자체에는 기록되지 않는 빠진 부분이 있었는데, 이걸로 메꾼다.
  - 이 extension은 `deprecated`/`predecessor`/`successor` 링크도 지원한다(미해결 참고).
- `pystac.extensions.file.FileExtension.ext(asset, add_if_missing=True).checksum = ...`으로 asset의 checksum을 기록한다.
  - asset이 이미 item에 붙어 owner가 있는 상태에서 호출해야 동작한다.

## 근거

- 진짜 collection으로 등록해야 카탈로그 등록 경로(pystac load-mutate-save, 버전 디렉터리, root catalog child link 교체)까지 검증할 수 있다.
  - 스모크테스트만으로는 이 부분이 검증되지 않는다.
- geovars 프로젝트가 환경 변수와 공간데이터 파이프라인을 다루므로, 관련 연구자료 서지는 나중에도 재사용 가치가 있다.
  - 레포 온보딩이나 related work 정리에 쓸 수 있다.

## 기각한 대안

- 논문 1편당 item 1개.
  - 본래 계획이었던 parquet 테이블 하나 구조와 맞지 않고, `sci:publications`가 리스트 필드라 테이블 하나에 여러 논문을 담는 쪽이 자연스럽다.
- 서지 데이터를 별도 CSV/YAML 파일로 분리.
  - 파이프라인 코드에는 하드코딩하는 쪽을 사용자가 명시적으로 선호했다.
  - 논문 수가 적을 때는 파일을 분리하는 게 과하다.
- PDF 원문도 asset으로 저장.
  - 저작권과 용량 문제로 기각했다.
  - 서지 메타데이터만 남긴다.
- `pystac.layout.TemplateLayoutStrategy`.
  - `normalize_hrefs`가 대상 객체를 트리의 root로 볼 때(`is_root=True`, 이 프로젝트처럼 collection을 그 자체로 저장하는 경우) `collection_template`을 무시하고 `BestPracticesLayoutStrategy`를 대신 쓴다는 사실을 확인했다.
  - item에는 템플릿이 적용되지만 collection에는 적용되지 않아 collection과 item의 경로가 어긋난다.
  - 우회하려면 루트 Catalog에서부터 전체를 `normalize_and_save`해야 하는데, 이는 이 프로젝트가 택한 증분 등록 모델과 정면으로 충돌한다.
  - 증분 등록은 한 collection의 서브트리만 쓰고 다른 collection은 건드리지 않는 방식이다([catalog-and-access.md](/decisions/catalog-and-access.md) "카탈로그 유지 절차").
  - 전체 재저장은 발행할 때마다 카탈로그 전체를 로드하고 다른 모든 collection 파일까지 재저장하게 만든다.
  - 그래서 커스텀 `register_collection()`을 그대로 유지한다.

## 발견한 버그 (pystac)

- `pystac.Collection.normalize_and_save(root_href, ...)`에서 `root_href`의 마지막 경로 조각에 `.`이 있으면(예: `MAJOR.MINOR.PATCH` 버전 문자열) pystac이 이를 파일명과 확장자로 오인해 그 조각을 통째로 잘라버린다.
  - `/a/b/0.1.0`의 self href가 `/a/b/collection.json`이 되어 `0.1.0`이 사라진다.
- root_href 끝에 `/`를 명시하면 회피된다.
  - `geovars.catalog.register_collection()`(`geovars/geovars/catalog/__init__.py`)에 이미 반영되어 있다.
  - 버전 디렉터리를 다루는 코드를 새로 짤 때 반드시 주의한다.
- `normalize_and_save(root_href, ...)`에 **상대경로** `root_href`를 넘기면, 버전 세그먼트가
  빠진 flat 경로(예: `<collection-id>/collection.json`)에 collection·item이 중복 생성된다
  (내용은 정상 위치의 것과 동일). 루트 `catalog.json`의 child link는 정상 경로를 가리켜 카탈로그
  자체는 깨지지 않지만, 커밋되지 않아야 할 stray 파일이 남는다.
  - `register_collection()`은 인자로 받은 `catalog_root`를 함수 안에서 `Path(...).resolve()`로
    절대경로화해 회피한다.

## 캐시 관련 주의사항

- `geovars` 패키지 소스(`geovars/geovars/`)를 고치고 로컬 pin(`file:///workspace/geovars`)으로
  재검증할 때, `.cache/uv/environments-v2/<script>-*`만 지우면 uv가 이전에 빌드해 둔 wheel
  캐시(`.cache/uv/wheels-v6` 등)를 그대로 재사용해 수정 전 코드로 계속 실행될 수 있다. 로그에
  `Building geovars @ file:///workspace/geovars` 줄이 없으면 재빌드가 안 된 것이다 — 이 경우
  `.cache/uv` 전체를 지우고 다시 실행한다.

## 미해결

- license 정책 — 레포와 데이터 전체의 라이선스가 정해지면 `"proprietary"` 임시값을 교체해야 한다. collection별 개별 확인 규칙은 [/decisions/license-review.md](/decisions/license-review.md)에 있다.
- `geovars` 패키지의 GitHub 호스팅 pin 검증 — push 이후 실제 GitHub 호스팅 pin이 동작하는지 별도로 확인해야 한다.
- 서지 데이터가 늘어나 CSV/YAML 분리가 아쉬워지면 그때 재검토한다(YAGNI).
- `VERSION`/`EXPERIMENTAL`/`DEPRECATED` 모듈 상수를 필수화하는 작업은 `.claude/skills/write-pipeline-script/SKILL.md`에서 마무리했다. `predecessor`/`successor`(새 버전 발행 시 옛 버전에 forward-pointer를 붙이는 작업, [/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md))는 실행 시점에 이전 버전을 참조해야 해서 여전히 미해결이다.

## 관련

- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)
- [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)
- [/decisions/reproducibility.md](/decisions/reproducibility.md)
- [/decisions/secrets-and-s3-client.md](/decisions/secrets-and-s3-client.md)
- [/decisions/cloudpathlib-cache-pattern.md](/decisions/cloudpathlib-cache-pattern.md)
- `.claude/skills/write-pipeline-script/SKILL.md`

# Citations

1. STAC Scientific Citation extension — https://github.com/stac-extensions/scientific
2. STAC File Info extension — https://github.com/stac-extensions/file
3. DOI 10.11108/kagis.2024.27.3.060 — https://doi.org/10.11108/kagis.2024.27.3.060
