---
type: decision
title: 시크릿 관리와 S3 호환 클라이언트 — .env 위치, boto3+cloudpathlib, 벤더 중립 명명, sign() 유예
description: Cloudflare R2 연동 확인을 위해 .env/.env.template 위치·컨테이너 전달 방식·클라이언트 조합을 확정. 환경변수는 R2가 아니라 S3 호환 API 기준으로 벤더 중립 명명해 향후 다른 S3 호환 스토리지로 전환 가능성을 열어둠. planetary_computer식 sign() 헬퍼는 추후 과제로 미룸.
tags: [secrets, env, dotenv, s3, r2, cloudflare, boto3, cloudpathlib, infrastructure, pipeline]
timestamp: 2026-07-21
---

# 시크릿 관리와 S3 호환 클라이언트

`/grill-me` 세션에서 하나씩 확정. Cloudflare 연동 범위는 **R2 오브젝트 스토리지만**
(Workers/Pages 등 다른 Cloudflare 서비스는 범위 밖). 실제 스토리지는 지금도 앞으로도
당분간 **Cloudflare R2**([/decisions/infrastructure.md](/decisions/infrastructure.md))다 —
아래 "벤더 중립 명명"은 스토리지를 바꾸기로 한 결정이 아니라, 순전히 **이름 짓기**
결정이다.

## 결정

- **`.env`/`.env.template`는 레포 루트**에 둔다. `.env`는 git-ignored(이미
  `.gitignore`에 등록됨), `.env.template`는 git 커밋.
- **비-비밀 값은 `.env.template`에 실제 값으로 커밋**한다 — 버킷명·엔드포인트는
  [/decisions/infrastructure.md](/decisions/infrastructure.md)에서 이미 비-비밀로
  분류됨. 키(`GEOVARS_S3_ACCESS_KEY_ID`/`GEOVARS_S3_SECRET_ACCESS_KEY`)만 빈칸.
- **환경변수·헬퍼 이름은 `R2`가 아니라 `GEOVARS_S3_*`로 벤더 중립 명명**
  (`BUCKET_NAME`/`ENDPOINT_URL`/`ACCESS_KEY_ID`/`SECRET_ACCESS_KEY`,
  캐시는 `GEOVARS_S3_CACHE_DIR`/`geovars.pipeline.s3_cache_dir()`/`.cache/s3/`) —
  버킷·엔드포인트·액세스키·시크릿키 구성은 R2든 다른 S3 호환 스토리지든 동일하므로,
  후임자가 R2가 아닌 다른 S3 호환 스토리지로 전환해도 이름을 바꿀 필요가 없게 한다.
  최초엔 `GEOVARS_R2_*`로 시작했다가 이 이유로 당일 뒤집었다(발행 전 draft라
  "정정"이 아니라 그냥 고쳐 씀,
  [/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)의
  in-place 금지 규칙은 이미 발행된 STAC 산출물 대상이라 여기 해당 없음). 기존
  `GEOVARS_CACHE_ROOT`/`GEOVARS_DUCKDB_CACHE_DIR`/`GEOVARS_SCRATCH_DIR`는 스토리지
  벤더와 무관해 그대로 둠.
- **`load_dotenv()`는 공용 헬퍼 없이 각 스크립트가 개별 호출**한다. 지금은 소비자가
  하나뿐이라 공용화가 이르다(YAGNI).
- **컨테이너 안 자격증명 전달은 `run.py` 수정 없이 bind mount로 자동 노출**된다 —
  `pipeline/run.py`가 이미 레포 전체를 `/workspace`로 bind mount하므로, 루트
  `.env`는 별도 `-e` 주입 없이 `/workspace/.env`로 그대로 보인다. 스크립트가 직접
  `load_dotenv()`로 읽는다.
- **클라이언트는 `boto3` + `cloudpathlib[s3]` 조합**, `geovars/pyproject.toml`의
  `pipeline` extra에 추가. `cloudpathlib`의 로컬 캐시 기능이 `GEOVARS_S3_CACHE_DIR`/
  read-through 미러 개념과 맞아떨어진다
  ([/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)의
  `.cache/s3/`). 향후 presigned URL이 필요해지면 `cloudpathlib`이 감싸는 `boto3`
  클라이언트에 바로 접근 가능.
- **planetary Computer식 `sign()` 헬퍼(자격증명을 한 곳에 모으고 나머지는 서명된
  URL만 받는 패턴, 참고:
  https://planetarycomputer.microsoft.com/docs/concepts/sas/)는 추후 과제로 미룸.**
  오늘은 "연결이 되는지"만 최소 확인.
  - 단, 클라이언트 코드가 `pipeline/` 전용이 아니라 **`geovars` 패키지도 직접
    접근 가능해야 한다**는 방향은 지금 확정 — `sign()`을 나중에 만들 때 어느
    컴포넌트든 자격증명을 직접 들지 않고 이 헬퍼를 통하게 하려는 의도.
- **연결 확인은 일회성 임시 PEP723 스크립트**(`pipeline/process/_r2_smoketest.py`)로
  검증하고 확인 후 스크립트+lock을 삭제 — flat 레이아웃을 실제 collection이 아닌
  파일로 오염시키지 않는다(이전 `run.py` 실행경로 검증 선례와 동일 패턴,
  [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)의
  "smoketest로 실제 실행 검증" 참고).
  - 실제로 `boto3.list_objects_v2` + `cloudpathlib.S3Path` 둘 다 R2(`bucket=geovars`)
    연결 성공 확인함(2026-07-21) — 최초 `GEOVARS_R2_*` 명명, 이후 `GEOVARS_S3_*`로
    전환한 뒤에도 재확인 완료.

## 근거

- 비밀(계정 키)과 비-비밀(버킷명·엔드포인트·자격증명 발급처)의 경계는 이미
  [/decisions/infrastructure.md](/decisions/infrastructure.md)에서 확정되어 있었고,
  이번 결정은 그 경계를 `.env`/`.env.template` 파일 분리에 그대로 매핑한 것뿐이다.
- 루트 위치 선택은 `pipeline/`(컨테이너 내 처리)과 `geovars`(향후 대시보드·`sign()`)
  둘 다 같은 자격증명을 공유해야 한다는 판단에서 나옴 — 단일 소스, 중복 관리
  비용 회피.
- 벤더 중립 명명(`S3`)은 순수 이름 짓기 비용이라 사실상 공짜에 가까운 선견(guard)이다
  — 버킷/엔드포인트/액세스키/시크릿키라는 네 개념 자체가 S3 API 표준이지 R2 고유가
  아니므로, 지금 이름을 R2로 박아두면 나중에 다른 S3 호환 스토리지로 옮길 때 코드
  전체의 이름을 바꿔야 하는 반면 지금 바꾸면 그 비용이 없다.

## 기각한 대안

- **`pipeline/` 워크스페이스 전용 `.env`** — "컴포넌트 자기완결" 원칙엔 더 맞지만,
  `geovars` 패키지도 향후 스토리지에 직접 접근(`sign()`)하게 될 예정이라 시크릿
  중복·드리프트 위험이 커서 기각.
- **`run.py`가 `-e KEY=VALUE`로 시크릿 주입** — 기존 `GEOVARS_S3_CACHE_DIR` 같은
  비-비밀 경로는 이 방식이 맞지만, 시크릿은 `docker inspect`/컨테이너 메타데이터에
  평문으로 남는 노출 경로가 생겨 기각. bind mount로 이미 파일이 보이므로 불필요.
- **`.env.template`의 비-비밀 값도 빈칸으로 통일** — 버킷명·엔드포인트는 이미 비밀이
  아니라고 결정되어 있어([/decisions/infrastructure.md](/decisions/infrastructure.md)),
  굳이 빈칸으로 둘 이유가 없고 오히려 새 개발자의 온보딩 비용만 늘어 기각.
- **환경변수·헬퍼 이름에 `R2`를 그대로 유지** — 실제 스토리지가 지금 R2인 것과, 그
  사실을 코드 전체 이름에 박아두는 것은 별개 문제. 버킷/엔드포인트/키 구성이
  S3 호환 API 표준이라 이름을 일반화해도 잃는 게 없어 기각(최초엔 이렇게 갔다가
  당일 뒤집음).
- **오늘 `sign()`까지 설계·구현** — 오늘 범위를 "연결 확인"으로 좁히기로 함(YAGNI).
  설계는 실제 처리 스크립트가 게이트된 asset을 읽어야 하는 시점에.

## 미해결

- `sign()` 헬퍼의 정확한 설계 — 어느 `geovars` extra에 둘지, presigned URL 만료
  시간, `pipeline/`과 `geovars.catalog` 양쪽에서 어떻게 재사용할지.
- `geovars.pipeline.s3_cache_dir()`를 실제 `cloudpathlib.S3Client(local_cache_dir=...)`
  기반으로 구현하는 작업 — 지금은 스텁만 있고 실제 처리 스크립트에서 아직 안 씀.
- 스토리지를 실제로 다른 S3 호환 벤더로 옮길 계획은 없음 — 이름만 중립화했을 뿐,
  전환 자체는 아직 가상의 미래 시나리오.

## 관련

- [/decisions/infrastructure.md](/decisions/infrastructure.md)
- [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md)
- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)

# Citations

1. Planetary Computer SAS 서명 개념 — https://planetarycomputer.microsoft.com/docs/concepts/sas/
