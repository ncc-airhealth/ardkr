---
type: decision
title: 시크릿 관리와 S3 호환 클라이언트 — .env 위치, boto3+cloudpathlib, 벤더 중립 명명, sign() 유예
description: Cloudflare R2 연동 확인을 위해 .env/.env.template 위치·컨테이너 전달 방식·클라이언트 조합을 확정. 환경변수는 R2가 아니라 S3 호환 API 기준으로 벤더 중립 명명해 향후 다른 S3 호환 스토리지로 전환 가능성을 열어둠. planetary_computer식 sign() 헬퍼는 추후 과제로 미룸.
tags: [secrets, env, dotenv, s3, r2, cloudflare, boto3, cloudpathlib, infrastructure, pipeline]
timestamp: 2026-07-21
---

# 시크릿 관리와 S3 호환 클라이언트

- Cloudflare 연동 범위는 R2 오브젝트 스토리지만이고, Workers·Pages 같은 다른 서비스는 범위 밖이다.
- 실제 스토리지는 지금부터 당분간 계속 Cloudflare R2다 ([/decisions/infrastructure.md](/decisions/infrastructure.md)).
- 아래 "벤더 중립 명명"은 스토리지를 바꾸기로 한 결정이 아니라 순전히 이름 짓기 결정이다.

## 결정

- `.env`와 `.env.template`는 레포 루트에 둔다.
  - `.env`는 git 추적에서 제외한다 (이미 `.gitignore`에 등록).
  - `.env.template`는 git에 커밋한다.
- 비밀이 아닌 값은 `.env.template`에 실제 값으로 커밋한다.
  - 버킷명과 엔드포인트는 [/decisions/infrastructure.md](/decisions/infrastructure.md)에서 이미 비밀이 아닌 것으로 분류됐다.
  - 키(`GEOVARS_S3_ACCESS_KEY_ID`/`GEOVARS_S3_SECRET_ACCESS_KEY`)만 빈칸으로 둔다.
- 환경변수와 헬퍼 이름은 `R2`가 아니라 `GEOVARS_S3_*`로 벤더 중립적으로 짓는다.
  - `BUCKET_NAME`, `ENDPOINT_URL`, `ACCESS_KEY_ID`, `SECRET_ACCESS_KEY`가 그 예다.
  - 캐시 쪽은 `GEOVARS_S3_CACHE_DIR`, `geovars.pipeline.s3_cache_dir()`, `.cache/s3/`로 짓는다.
  - 버킷·엔드포인트·액세스키·시크릿키 구성은 R2든 다른 S3 호환 스토리지든 동일하므로, 후임자가 스토리지를 전환해도 이름을 바꿀 필요가 없다.
  - 기존 `GEOVARS_CACHE_ROOT`, `GEOVARS_DUCKDB_CACHE_DIR`, `GEOVARS_SCRATCH_DIR`는 스토리지 벤더와 무관해 그대로 둔다.
- `load_dotenv()`는 공용 헬퍼 없이 각 스크립트가 개별 호출한다.
  - 지금은 소비자가 하나뿐이라 공용화가 이르다 (YAGNI).
- 컨테이너 안 자격증명 전달은 `run.py` 수정 없이 bind mount로 자동 노출된다.
  - `pipeline/run.py`가 이미 레포 전체를 `/workspace`로 bind mount하므로, 루트 `.env`가 `/workspace/.env`로 그대로 보인다.
  - 스크립트가 직접 `load_dotenv()`로 읽는다.
- 클라이언트는 `boto3`와 `cloudpathlib[s3]` 조합을 쓰고, `geovars/pyproject.toml`의 `pipeline` extra에 추가한다.
  - `cloudpathlib`의 로컬 캐시 기능은 `GEOVARS_S3_CACHE_DIR`의 read-through 미러 개념과 맞아떨어진다 ([/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)의 `.cache/s3/`).
  - 향후 presigned URL이 필요해지면 `cloudpathlib`이 감싸는 `boto3` 클라이언트에 바로 접근할 수 있다.
- Planetary Computer식 `sign()` 헬퍼는 추후 과제로 미룬다.
  - 자격증명을 한 곳에 모으고 나머지는 서명된 URL만 받는 패턴이다.
  - 오늘은 연결이 되는지만 최소로 확인한다.
  - 다만 클라이언트 코드는 `pipeline/` 전용이 아니라 `geovars` 패키지도 직접 접근 가능해야 한다는 방향은 지금 확정한다.
  - `sign()`을 나중에 만들 때 어느 컴포넌트든 자격증명을 직접 보유하지 않고 이 헬퍼를 통하게 하려는 의도다.
- 연결 확인은 일회성 임시 PEP723 스크립트(`pipeline/process/_r2_smoketest.py`)로 검증하고, 확인 후 스크립트와 lock을 삭제한다.
  - flat 레이아웃을 실제 collection이 아닌 파일로 오염시키지 않기 위해서다.
  - 이전 `run.py` 실행경로 검증 선례와 동일한 패턴이다 ([/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)의 "smoketest로 실행 경로를 검증했다").
  - `boto3.list_objects_v2`와 `cloudpathlib.S3Path` 둘 다 R2(`bucket=geovars`) 연결 성공을 확인했다 (2026-07-21).

## 근거

- 비밀(계정 키)과 비밀이 아닌 것(버킷명·엔드포인트·자격증명 발급처)의 경계는 이미 [/decisions/infrastructure.md](/decisions/infrastructure.md)에서 정해져 있었다.
  - 이번 결정은 그 경계를 `.env`/`.env.template` 파일 분리에 그대로 매핑한 것뿐이다.
- 루트 위치를 고른 이유는 `pipeline/`의 컨테이너 내 처리와 `geovars`의 향후 대시보드·`sign()`이 같은 자격증명을 공유해야 하기 때문이다.
  - 단일 소스를 유지하면 중복 관리 비용을 피할 수 있다.
- 벤더 중립 명명(`S3`)은 이름을 짓는 비용만 드는 선제 조치라 공짜에 가깝다.
  - 버킷·엔드포인트·액세스키·시크릿키라는 네 개념 자체가 S3 API 표준이지 R2 고유가 아니다.
  - 지금 이름을 R2로 고정하면 나중에 다른 S3 호환 스토리지로 옮길 때 코드 전체의 이름을 바꿔야 하지만, 지금 바꾸면 그 비용이 없다.

## 기각한 대안

- `pipeline/` 워크스페이스 전용 `.env` — "컴포넌트 자기완결" 원칙엔 더 맞지만, `geovars` 패키지도 향후 `sign()`으로 스토리지에 직접 접근할 예정이라 시크릿 중복·드리프트 위험이 커서 기각.
- `run.py`가 `-e KEY=VALUE`로 시크릿 주입 — 비밀이 아닌 경로(`GEOVARS_S3_CACHE_DIR` 등)엔 맞지만, 시크릿은 `docker inspect`나 컨테이너 메타데이터에 평문으로 남는 노출 경로가 생겨 기각.
  - bind mount로 이미 파일이 보이므로 불필요하다.
- `.env.template`의 비밀이 아닌 값도 빈칸으로 통일 — 버킷명·엔드포인트는 이미 비밀이 아니라 빈칸으로 둘 이유가 없고, 오히려 새 개발자의 온보딩 비용만 늘어 기각.
- 환경변수·헬퍼 이름에 `R2`를 그대로 유지 — 버킷·엔드포인트·키 구성이 S3 호환 API 표준이라 이름을 일반화해도 잃는 게 없어 기각.
- 오늘 `sign()`까지 설계·구현 — 오늘 범위를 연결 확인으로 좁히기로 했다 (YAGNI). 설계는 실제 처리 스크립트가 게이트된 asset을 읽어야 하는 시점에 한다.

## 미해결

- `sign()` 헬퍼의 정확한 설계가 남아 있다.
  - 어느 `geovars` extra에 둘지.
  - presigned URL 만료 시간을 얼마로 할지.
  - `pipeline/`과 `geovars.catalog` 양쪽에서 어떻게 재사용할지.

`geovars.pipeline.s3_cache_dir()`를 실제 `cloudpathlib.S3Client(local_cache_dir=...)` 기반으로 구현하는 작업은 [/decisions/cloudpathlib-cache-pattern.md](/decisions/cloudpathlib-cache-pattern.md)에서 마무리했다.

## 관련

- [/decisions/infrastructure.md](/decisions/infrastructure.md)
- [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)
- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)
- [/decisions/cloudpathlib-cache-pattern.md](/decisions/cloudpathlib-cache-pattern.md)

# Citations

1. Planetary Computer SAS 서명 개념 — https://planetarycomputer.microsoft.com/docs/concepts/sas/
