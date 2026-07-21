# Log

## 2026-07-21

- Update — `geovars-references` 세 번째 리뷰 반영: `REFERENCES`(클래스 변수)를
  `references`(`@property`)로 분리(클래스 변수엔 collection 메타데이터만), duckdb→pandas
  로 단순화(`pd.DataFrame(...).to_parquet()`), STAC extension을 pystac 공식 클래스
  (`ScientificExtension`/`VersionExtension`/`FileExtension`)로 교체 — 그 결과 collection
  에 `version` 필드가 처음으로 STAC 메타데이터에 기록되고, `cite-as` link도 자동 생성됨.
  [geovars-references-collection](/decisions/geovars-references-collection.md)
  "세 번째 리뷰 반영" 참고.
- Update — 사용자 리뷰로 `geovars-references` 구현을 두 번째 `/grill-me` 라운드로 개선:
  버전 디렉터리를 `version=<version>`(Hive 스타일)로, S3 업로드 전 스테이징을
  `.cache/s3/<key 그대로>`(양방향 미러)로, `pipeline/process/*.py`를 `Processor` 클래스
  공식 템플릿으로, PEP723 의존성을 정확한 버전(`==`)으로 고정. lock 파일을 별도 경로로
  옮기는 안은 **uv가 지원하지 않음을 실제 확인 후 기각**(스크립트 옆 유지). pystac
  `TemplateLayoutStrategy` 도입도 검토 후 기각(증분 등록 모델과 충돌, 실제 테스트로
  확인). [geovars-references-collection](/decisions/geovars-references-collection.md)
  "두 번째 grilling 라운드", [pipeline-architecture](/decisions/pipeline-architecture.md)
  "Processor 클래스 템플릿", [catalog-and-access](/decisions/catalog-and-access.md)
  "collection 버전 디렉터리 구현" 참고.
- Creation — [geovars-references-collection](/decisions/geovars-references-collection.md) +
  첫 실제 STAC collection `geovars-references` 등록(`stac-metadata/geovars-references/0.1.0/`):
  geovars 프로젝트 관련 연구자료(논문) 서지, item 1개(테이블) + duckdb→parquet asset,
  STAC Scientific Citation extension(`sci:publications`)으로 인용정보 기록. 첫 항목은
  DOI `10.11108/kagis.2024.27.3.060`(김원경 외, 2024). `pipeline/process/
  geovars-references.py`가 처리 스크립트. S3 업로드 후 `file:checksum`(Multihash)을
  실제 바이트 해시로 재검증 완료(일치 확인).
  - `geovars.pipeline`에 `multihash_sha256()`/`upload_asset()`, `geovars.catalog`에
    `register_collection_version()` 신규 구현(첫 실사용).
  - `geovars` 공용 유틸을 **처음으로 git-commit pin**해 소비(`git+file:///workspace@
    <commit>#subdirectory=geovars` — 아직 GitHub push 전이라 로컬 pin). 컨테이너에
    `git`이 없어 `pipeline/images/2026.07.21/Dockerfile`에 추가(draft 이미지 in-place
    수정). 세부: [pipeline-architecture](/decisions/pipeline-architecture.md)
    "git-commit pin 실사용 검증".
  - **pystac 버그 발견·수정**: `normalize_and_save(root_href)`가 root_href의 마지막
    조각에 `.`이 있으면(버전 문자열 `0.1.0` 등) 파일명+확장자로 오인해 잘라버림 —
    trailing `/`로 회피. [catalog-and-access](/decisions/catalog-and-access.md)
    "collection 버전 디렉터리 구현"에 기록, `ensure_ascii=False` 재직렬화 TODO도 이
    김에 해소.

- Creation — [secrets-and-s3-client](/decisions/secrets-and-s3-client.md): Cloudflare R2
  연동을 위한 시크릿 관리 확정. `.env`/`.env.template` 레포 루트(pipeline/과 geovars 패키지가
  자격증명 공유), 비-비밀 값(버킷명·엔드포인트)은 `.env.template`에 실제 값 커밋, 컨테이너
  전달은 run.py 수정 없이 bind mount로 자동 노출, 클라이언트는 `boto3`+`cloudpathlib[s3]`
  (`geovars/pyproject.toml`의 `pipeline` extra에 추가). planetary_computer식 `sign()` 헬퍼는
  추후 과제로 유예. 임시 PEP723 스모크테스트(`pipeline/process/_r2_smoketest.py`, 확인 후
  삭제)로 boto3·cloudpathlib 둘 다 R2(`bucket=geovars`) 연결 성공 확인.
- Update — 환경변수·헬퍼 이름을 `GEOVARS_R2_*`/`r2_cache_dir()`에서 **벤더 중립
  `GEOVARS_S3_*`/`s3_cache_dir()`**로 전환(`geovars.pipeline`, `pipeline/run.py`,
  `.env`/`.env.template`, `.cache/s3/`) — 실제 스토리지는 여전히 Cloudflare R2([infrastructure](/decisions/infrastructure.md))
  지만, 버킷·엔드포인트·키 구성이 S3 호환 API 표준이라 후임자가 다른 S3 호환 스토리지로
  전환할 가능성을 이름 비용 없이 열어둠. 전환 후 재확인(smoketest)까지 완료.
  [secrets-and-s3-client](/decisions/secrets-and-s3-client.md) "벤더 중립 명명" 참고.
- Update — [infrastructure](/decisions/infrastructure.md): TBD였던 버킷명(`geovars`)·
  엔드포인트·스토리지 티어(일반 클래스)·자격증명 발급 요청 대상을 실제 값으로 채움.
- Creation — `pipeline/run.py` 컨테이너 실행 구현: 레포 volume mount(스크립트 즉시 반영,
  이미지 재빌드 불필요), `docker image inspect` 후 없으면 로컬 빌드 폴백, lock_action에 따라
  GENERATE/RELOCK만 `uv lock` 먼저 실행 후 항상 `uv run --frozen`, CLI
  `python pipeline/run.py <collection-id> [--relock]`. 임시 smoketest 스크립트로 전체 경로
  (빌드 폴백→lock 생성→실행, 재실행 시 FROZEN) 검증 완료. 파이프라인 아키텍처의 "실행기
  진입 방식·인자" 미해결 항목 해소. `.gitignore`도 `cache/`→`.cache/`로 정리.
- Creation — `.cache/` 통합 캐시 레이아웃(`uv/`·`duckdb/`·`r2/`·`pipeline/<collection-id>/`),
  컨테이너엔 `/cache`로 한 번만 mount + env var로 경로 노출. "캐시는 순수 가속 장치, 지워도
  같은 결과가 나와야 한다"는 불변식 명시. `geovars.pipeline`에 `cache_root()`/
  `r2_cache_dir()`/`duckdb_cache_dir()`/`scratch_dir()` 헬퍼 추가. 세부는
  [pipeline-architecture](/decisions/pipeline-architecture.md) "CLI 계약과 컨테이너 실행 구현" ·
  "캐시" 절.
- Creation — `stac-metadata/catalog.json`: 빈 root STAC 카탈로그를 pystac
  `normalize_and_save(catalog_type=SELF_CONTAINED)`로 생성. `ABSOLUTE_PUBLISHED` 대신
  `SELF_CONTAINED`을 택한 이유와, 한국어 diff 리뷰를 위한 `ensure_ascii=False` 재직렬화 필요성을
  [catalog-and-access](/decisions/catalog-and-access.md) "root catalog.json 구현" 절에 기록.
- Creation — `pipeline/images/2026.07.21/`: 첫 시스템 환경 정의(`pixi.toml`+`pixi.lock`+
  `Dockerfile`, python/gdal/geos/proj/uv). Dockerfile은 pixi 설치 스크립트 기반 2-stage 빌드.
  같은 날 안에 정규 arch를 `linux/amd64`에서 `linux/arm64`로 뒤집음(팀이 주로 Apple Silicon
  Mac에서 작업 — 네이티브 실행 우선, 아직 미발행 draft라 in-place 수정). arm64로 빌드·실행
  검증(`uname -m`=aarch64, gdal/python/uv 정상) 완료. 세부는
  [pipeline-architecture](/decisions/pipeline-architecture.md) "단일 정규 arch" · "첫 이미지" 절.
- Creation — [ponytail-plugin](/decisions/ponytail-plugin.md): Ponytail(코드 최소주의
  Claude Code 플러그인)을 프로젝트 스코프(`.claude/settings.json`의
  `extraKnownMarketplaces`+`enabledPlugins`)로 도입. pipeline/process/*.py의 flat/
  self-contained 원칙과 "재사용 우선" 규칙 충돌 가능성은 미해결로 남김.
- Creation — [pipeline-architecture](/decisions/pipeline-architecture.md): 모노레포 구조,
  자기완결 처리 스크립트(PEP723+스크립트별 lock), Docker+pixi 시스템 환경 고정(최대
  durability·이미지 보존), pipeline/ 실행기(`pipeline/run.py`), geovars 단일 패키지,
  flat 스크립트 + git commit provenance 재현.
- Creation — geovars 패키지 스캐폴드 + 레이아웃 확정: `geovars/`가 `pyproject.toml` 소유,
  임포트 패키지는 `geovars/geovars/`(한 겹 중첩, src-layout 대신). optional extras 분리
  (catalog/pipeline/dashboard/modeling), 코어는 의존성 0·지연 임포트. 실행기는
  `pipeline/run.py`로 이동(실행은 pipeline/ 워크스페이스 책임), geovars 콘솔 명령은 폐기.
  → [pipeline-architecture](/decisions/pipeline-architecture.md) 구조·실행 섹션 갱신.
- Update — 기존 결정 기록을 grilling 재검토 결과에 맞게 정정:
  [knowledge-architecture](/decisions/knowledge-architecture.md)(정정 provenance는 자유 서술로,
  `[correction]` 마커 폐기), [reproducibility](/decisions/reproducibility.md)(코드 층·lock 강제
  재작성, `file:checksum`+R2 미러 명시), [versioning-and-corrections](/decisions/versioning-and-corrections.md)·
  [catalog-and-access](/decisions/catalog-and-access.md)·[governance-and-review](/decisions/governance-and-review.md)
  (`processing.py`→flat 스크립트·`stac-metadata/`·실행기 정합화).

## 2026-07-20

- Creation — OKF 번들 생성. `agent-native-refactoring` orphan 브랜치를 백지 씨앗으로 시작.
- Creation — [/principles.md](/principles.md): 세 가지 창립 원칙 기록.
- Creation — 의사결정 기록 7건 작성 (grilling 세션 결과):
  [knowledge-architecture](/decisions/knowledge-architecture.md),
  [versioning-and-corrections](/decisions/versioning-and-corrections.md),
  [reproducibility](/decisions/reproducibility.md),
  [catalog-and-access](/decisions/catalog-and-access.md),
  [governance-and-review](/decisions/governance-and-review.md),
  [knowledge-capture](/decisions/knowledge-capture.md),
  [infrastructure](/decisions/infrastructure.md).
