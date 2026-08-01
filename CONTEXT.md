# ardkr

연구팀 공공 공간데이터를 재현 가능한 처리 스크립트로 가공해 STAC 카탈로그로 발행하는 레포.

## Language

**생명주기**:
처리 스크립트가 따르는 고정된 단계 순서. process → verify_auto → verify_manual → publish.

**발행 (publish)**:
생명주기의 마지막 단계. digest를 확정해 `file:size`·`file:checksum`을 기록하고, 데이터 asset은 데이터 버킷에, STAC 메타데이터는 static self-contained로 open 버킷에, 썸네일은 open 버킷에 올린다. experimental이면 수행되지 않는다.

**experimental**:
collection이 정식 발행 전 실험 상태임을 나타내는 표식. 발행의 유일한 게이트. True이면 생명주기는 verify_manual까지 수행되고 publish는 중단된다.
_Avoid_: PUBLISH_MODE (폐기된 개념)

**수동 검증 (manual checklist)**:
자동으로 판정할 수 없는 항목을 사람이 미리 yes/no로 판정해 두는 생명주기 단계.

**버전 (version)**:
collection 단위로 매기는 semver. STAC 메타데이터와 원격 객체 경로의 파티션 단위.

**로컬 미러**:
원격 객체 저장소의 객체와 1:1 경로로 대응되는 로컬 파일시스템 캐시. 처리 스크립트의 산출물은 여기에 쓴다.

**accessor (.kr)**:
STAC 객체(Collection/Item/Asset)에 붙이는 ardkr 전용 동작의 네임스페이스.

**데이터 버킷**:
데이터 asset을 올리는 비공개 객체 저장소(물리명 geovars). 소비는 sign이나 자격증명을 거친다.
_Avoid_: 메인 버킷

**open 버킷**:
STAC 메타데이터를 static self-contained로 서빙하고 썸네일·공개 데이터셋을 올리는 공개 객체 저장소. sign 없이 읽힌다.

## 계획: pipeline 재설계

2026-07-31 합의. `ardkr.pipeline`을 생명주기 프레임워크로 재설계하고 `esri-mdl-dmz`를 첫 소비자로 맞춘다.

### 프레임워크 계약

- 생명주기 고정: `process → verify_auto → verify_manual → publish`
- publish 동작: digest 확정(`file:size`·`file:checksum`) → 데이터 asset은 데이터 버킷, STAC 메타데이터는 open 버킷에 static self-contained(root catalog 원격 갱신, `version={version}/` 누적), 썸네일은 open 버킷
- accessor `.kr`: `asset_href(filename)`은 Collection/Item에, `path`·`local_digest`·`remote_digest`·`publish`는 Asset에
- 객체 경로 스킴: `s3://{bucket}/{catalog.id}/{collection.id}/version={version}/assets/{filename}`. item asset은 `…/items/{item.id}/assets/{filename}`
- 수동 검증: `manual_checklist`의 False는 사람 미확인. build 중단, 사람이 True로 뒤집어 sign-off

### 모듈 경계

- `common`: Secrets (`s3`, `open` 각각 `S3Credentials`)
- `storage`: 연결 계층. `get_client(scope)`와 미래의 `sign`만 (순수 boto3 작업만). `Scope`는 StrEnum("s3" | "open"). cloudpathlib 제거
- `pipeline`: 생명주기 프레임워크. Builder·accessor·경로 스킴·digest·업로드 규약(객체 Metadata의 checksum)·STAC static 발행
- 의존 방향: `common ← storage ← pipeline`
- 카탈로그의 유일한 공개 위치는 open 버킷의 static STAC (`open-static-stac`)

### 소비자: esri-mdl-dmz

- 빌더 클래스명은 `PipelineCollection`, `collection`은 클래스 속성으로 정의
- `_add_mdl_asset`·`_add_dmz_asset`로 이름 통일, `self.collection.assets`로 명시 접근 (위임 없음)
- 좌표계 검증 `== EPSG`, extent bbox는 두 레이어 union으로 `process()`에서 갱신, `# fmt` 마커 위치 교정
