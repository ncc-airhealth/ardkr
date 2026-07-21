---
type: decision
title: 파이프라인 아키텍처 — 처리 스크립트·환경·실행
description: 모노레포 구조, 자기완결 처리 스크립트(PEP723+lock), Docker+pixi로 시스템 환경 고정, Python 래퍼 실행, geovars 단일 패키지. 버전 재현은 flat 스크립트 + git commit provenance.
tags: [pipeline, monorepo, pixi, docker, pep723, uv, reproducibility, geovars]
timestamp: 2026-07-21
---

# 파이프라인 아키텍처 — 처리 스크립트·환경·실행

옛 refactoring-plan에서 딸려왔던(그러나 이 프로젝트에서 재합의된 적 없던) 처리
스크립트·의존성·Docker·공용 유틸 전반을 백지에서 다시 논의해 확정한 기록.

## 모노레포 구조

```
geovars/                       # geovars 컴포넌트 (자기완결)
  pyproject.toml               #   패키지 정의 + optional extras
  geovars/                     #   임포트 패키지 (대시보드·파이프라인 유틸·카탈로그 검색·모델링)
pipeline/                      # 처리 실행 워크스페이스
  run.py                       #   실행기: image 해석 → 컨테이너 → lock → uv run
  images/<YYYY.MM.DD>/         #   시스템 환경 정의: pixi.toml + pixi.lock + Dockerfile
  process/<collection-id>.py   #   flat 처리 스크립트 (+ <collection-id>.py.lock)
stac-metadata/                 # STAC JSON (데이터 사실의 SSOT). 버전 차원은 여기
knowledge/                     # OKF 지식
.claude/                       # 에이전트 skills
.gitignore  CLAUDE.md  README.md
```

- **컴포넌트 자기완결**: 각 최상위 디렉토리는 동급 컴포넌트다. Python 패키징 설정은
  레포 루트가 아니라 `geovars/`가 소유하고(`geovars/pyproject.toml`), 임포트 패키지는
  `geovars/geovars/`에 둔다(src-layout 대신 한 겹 중첩). 루트는 "레포=패키지"가 아니라
  모노레포다.
- **실행 소유권**: 처리 스크립트를 실행하는 책임은 `pipeline/` 워크스페이스에 있다.
  실행기는 `pipeline/run.py`이며, geovars 패키지의 콘솔 명령이 아니다.

## 처리 스크립트 모델

- **자기완결 단일 파일** — 스크립트마다 PEP 723 인라인 의존성 선언 + 스크립트별 lock,
  `uv run --script`로 실행. 옛 스크립트를 안 건드리고 새 스크립트에서 최신 라이브러리 채택
  가능. (기각한 대안: 단일 공용 환경 / editable 로컬 참조 — 후자는 옛 스크립트가 최신 유틸을
  써서 재현성 파괴)
- **flat 레이아웃** — `pipeline/process/<collection-id>.py`. **파일명 = collection id**.
- **버전 차원은 스크립트가 아니라 `stac-metadata/`에** 둔다. `pipeline/process/`는 flat =
  최신 스크립트만.
- **버전 재현은 git commit 기반** — 각 발행 버전의 **STAC provenance에 그 버전을 생성한
  git commit + `image` 버전을 기록**한다. 재현 = 그 commit을 checkout(→ 그때의 스크립트+lock)
  → 보존된 image pull → 실행.
  - 기각한 대안: 버전별 스크립트 디렉토리(`version=<v>/`). commit provenance가 어차피 필요
    하므로(유틸·image가 그 시점 것이어야 함) 스크립트 복사본은 중복. flat + commit이 더 단순.
  - 감수한 트레이드오프: HEAD에서 모든 버전 스크립트를 나란히 보는 편의를 포기하는 대신,
    단순성 + 재현 메커니즘 단일화(commit pin)를 택함.

## 시스템 환경 — Docker + pixi (최대 durability)

- 두 층이 분리된다: **Docker**(바깥, OS 층까지 고정) + **pixi**(안, conda-forge에서
  GDAL/GEOS/PROJ/uv를 `pixi.lock`으로 고정). "pixi로 만든 환경을 담은 Docker 컨테이너".
- **최대 durability를 위해 빌드된 이미지를 레지스트리에 보존**(냉동; 데이터 삭제금지 정책의
  이미지판) — 10년 후 재현은 "레시피 rebuild"가 아니라 "얼려둔 OCI 이미지 pull"이 가장 튼튼.
  빌드 정의(`Dockerfile` + `pixi.lock`)도 레포에 커밋해 rebuild도 가능하게 둔다.
- **`pipeline/images/<YYYY.MM.DD>/`** = `pixi.toml` + `pixi.lock` + `Dockerfile` (빌드 정의).
  식별자는 `YYYY.MM.DD` (같은 날 두 번 갱신 시 `-2` 접미사).
- **스크립트가 자기 시스템 환경을 pin** — PEP 723 블록 안 커스텀 테이블에:

  ```python
  # /// script
  # dependencies = ["duckdb", "pyproj"]
  #
  # [tool.geovars]
  # image = "2026.07.20"        # → pipeline/images/2026.07.20/
  # ///
  ```

  시스템 deps를 올리면 새 `images/<날짜>/`를 만들고, 옛 스크립트는 계속 옛 `image`를 가리킴
  ([/decisions/reproducibility.md](/decisions/reproducibility.md)의 시스템 층 pin).
- **단일 정규 arch `linux/arm64`** — 한 arch = 결정론적 출력(어떤 arch를 고르든 이 성질은
  유지된다). **팀이 주로 Apple Silicon Mac에서 작업**하므로, 그 환경에서 에뮬레이션 없이
  네이티브로 빌드·실행되는 쪽을 정규로 택함(2026-07-21, 최초엔 `linux/amd64`로 시작했다가
  당일 뒤집음 — 발행 전 draft 상태라 "정정"이 아니라 그냥 고쳐 씀,
  [/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)의
  in-place 금지 규칙은 이미 발행된 STAC 산출물 대상이라 여기 해당 없음).
  x86_64 호스트(인텔 맥·클라우드 러너 등)에서는 반대로 에뮬레이션이 필요해진다 — CI를
  안 쓰기로 확정했으므로 이 비용은 주로 사람이 드물게 x86_64에서 빌드/실행할 때만 발생.
  대량 처리 속도나 팀 구성이 바뀌면(x86_64 비중이 늘면) 재검토.
  (기각: multi-arch — cross-arch 부동소수점/SIMD 출력 차이 위험(같은 스크립트가 arch에 따라
  다른 결과를 낼 수 있음). `linux/amd64` 유지 — 팀 실사용 환경(Apple Silicon)과 안 맞아
  매 빌드/실행에서 불필요한 에뮬레이션 비용을 짐. plain Dockerfile+apt — apt 미러가 옛 버전을
  지워 rebuild 불가. pixi-only — OS 층 미고정 + pixi 신생 도구 리스크.)

### 첫 이미지 `pipeline/images/2026.07.21/` (2026-07-21)

아직 어떤 처리 스크립트도 없는 상태에서, 뼈대 작업의 일환으로 최초 이미지를 만들었다. 같은 날
안에 정규 arch를 `linux/amd64`에서 `linux/arm64`로 뒤집었다(위 "단일 정규 arch" 참고) — 아래는
최종(arm64) 상태.

- **`pixi.toml`**: `platforms = ["linux-aarch64"]`(conda-forge에서 리눅스 ARM64를 가리키는
  이름), `dependencies`에 `python=3.12.*`, `gdal>=3.13,<4`, `geos>=3.14,<4`, `proj>=9.8,<10`,
  `uv>=0.11,<0.12` (2026-07-21 시점 conda-forge 최신 리졸브 — amd64로 처음 `pixi add`했을 때와
  버전이 완전히 동일하게 aarch64에서도 solve됨을 확인). 향후 스크립트가 실제로 필요로 하는
  라이브러리가 늘면 이 최초 이미지에 추가하거나, 필요시 새 날짜 디렉토리를 판다.
- **`pixi.lock` 생성은 `pixi lock`으로 충분** — 설치 없이 solve만 하므로, 개발자가 x86_64
  머신에서 작업해도 `linux-aarch64` lock을 문제없이 만들 수 있다(반대 방향도 마찬가지). 에뮬레이션은
  실제 `docker build`/`docker run` 시점, 그것도 실행 host arch와 이미지 arch가 다를 때만 필요하다.
- **`Dockerfile`은 2-stage**:
  1. build 스테이지 — 공식 설치 스크립트(`curl -fsSL https://pixi.sh/install.sh | sh`)로
     pixi 자체를 설치한 뒤 `pixi install --locked` 실행. (기각한 대안: `ghcr.io/prefix-dev/pixi`
     사전빌드 베이스 이미지 — 정확한 태그가 존재·유지되는지 확인 없이 고정하는 리스크를
     피하려고 설치 스크립트 방식을 택함.) 설치 스크립트는 실행 중인 arch를 자동 감지해 맞는
     pixi 바이너리를 받으므로 arm64 전환 때 이 줄은 그대로 두었다.
  2. 최종 스테이지 — `build`에서 만들어진 `.pixi/envs/default`만 복사해 런타임 이미지를 슬림하게
     유지(pixi 자체·빌드 캐시는 최종 이미지에 남지 않음).
  - 모든 `FROM`에 `--platform=linux/arm64`를 명시적으로 박아, x86_64 호스트에서 빌드해도 항상
    정규 arch(linux/arm64)로 고정되게 했다(위 "단일 정규 arch" 결정과 실제로 일치시킴).
  - pixi 버전은 `pixi.lock`을 만든 버전(`v0.65.0`)으로 install 스크립트에 명시 고정 — "latest"로
    두면 컨테이너 안 pixi가 더 최신 lock 포맷(v7 등)을 요구해 불필요한 재-lock을 유발할 수 있음을
    실제로 확인했다(최초 빌드 시 `PIXI_VERSION` 미지정 → v7 업그레이드 경고 발생 → 버전 고정 후
    재현).
  - Apple Silicon Mac(호스트=arm64)에서 `docker build --platform linux/arm64` 후 `docker run`으로
    `uname -m`(`aarch64`, 에뮬레이션 경고 없음) / `gdalinfo --version`(GDAL 3.13.1) /
    `python3 --version`(3.12.13) / `uv --version`(0.11.29, `aarch64-unknown-linux-gnu` 빌드)
    네이티브 정상 동작 검증 완료.

## 실행 — pipeline/ 워크스페이스의 실행기 (크로스플랫폼)

- 처리 스크립트 실행은 **`pipeline/` 워크스페이스의 책임**이다. 실행기 `pipeline/run.py`
  (Python, stdlib 부트스트랩)로 Windows·Mac·Linux에서 동일 실행. (`.sh`는 Windows 네이티브
  불가라 기각. geovars 패키지의 콘솔 명령으로 두는 방식도 기각 — 실행은 파이프라인 관심사지
  라이브러리 관심사가 아니다.) 컨테이너 없이도 도는 얇은 부트스트랩으로 chicken-egg 회피.
- 실행기 한 번 실행: ① 스크립트 상단 `image` 읽기 → 그 컨테이너 진입 → ② lock 처리 →
  ③ `uv run --script`.
- **lock 동작 규칙**: **없으면 컨테이너 안에서 생성 / 있으면 frozen 그대로 사용 / 재-lock은
  명시적 플래그로만**(`--relock`). 매 실행 자동 재생성 금지(pin 무효화 방지). 재-lock은
  의존성을 의도적으로 바꾸는 것이므로, 산출물이 발행됐다면 **새 버전으로 취급**.
- **lock 커밋은 필수**(규칙). **CI는 도입하지 않기로 확정** — 커밋 여부를 확인하는 자동
  게이트는 없다. 위반은 사후 발견에 의존한다
  ([/decisions/reproducibility.md](/decisions/reproducibility.md)).

### CLI 계약과 컨테이너 실행 구현 (2026-07-21)

위 "실행기 진입 방식·인자" 미해결을 실제로 구현하며 확정했다.

- **CLI**: `python pipeline/run.py <collection-id> [--relock]`. `argparse` 기반, `--relock`
  없으면 기존 lock을 그대로 쓰고 없으면 생성한다(위 lock 동작 규칙 그대로).
- **컨테이너 진입**: 레포 전체를 `/workspace`로 bind mount(`-w /workspace`) — 스크립트를
  이미지 안에 굽지 않으므로, `pipeline/process/<id>.py`를 고치고 다시 실행하면 **이미지
  재빌드 없이** 바로 반영된다.
- **이미지 확보**: `docker image inspect`로 로컬에 있는지 먼저 확인하고, 있으면 그대로
  쓴다(매 실행마다 빌드/pull 안 함 — 이미지 빌드는 `pipeline/images/<날짜>/` 버전이 바뀔 때만
  드물게 발생). 없으면 `pipeline/images/<image>/`에서 로컬 빌드로 폴백한다 — "보존된 이미지
  pull"이 정규 경로지만 레지스트리 선택이 아직 미해결이라, 그게 정해지기 전까지의 임시
  경로다.
- **lock 처리는 별도 컨테이너 실행으로 분리**: GENERATE/RELOCK이면 먼저 `uv lock --script`를
  한 번 실행(끝나면 커밋하라고 안내 출력)하고, 그 다음 항상 `uv run --frozen --script`로
  실행한다. FROZEN(가장 흔한 반복 실행 경로)이면 컨테이너 실행이 한 번뿐이다.
- **smoketest로 실제 실행 검증**: 임시 PEP 723 스크립트로 `python pipeline/run.py <id>` 전
  경로(이미지 로컬 빌드 폴백 → lock 생성 → 실행, 그리고 재실행 시 FROZEN 경로)를 실제로
  돌려 확인.

### 캐시 — `.cache/` (2026-07-21)

빠른 수정→재실행 반복 워크플로우의 병목을 없애기 위해 도구별 캐시를 레포 루트
`.cache/`(git-ignored) 밑에 모으고, 컨테이너엔 통째로 `/cache`로 한 번만 mount한다.

```
.cache/
  uv/                       # uv wheel/venv 캐시 (UV_CACHE_DIR)
  duckdb/                   # duckdb extension·spill(temp_directory)
  r2/                       # R2 객체 로컬 read-through 미러
  pipeline/<collection-id>/ # 스크립트별 중간산출물·스크래치
```

- **불변식 — 캐시는 순수 가속 장치, 입력이 아니다**: `.cache/`를 통째로 지워도 재실행하면
  **같은 결과**가 나와야 한다(느려질 뿐). `r2/`는 이미 R2에 박제되고 STAC `file:checksum`으로
  고정된 원본의 로컬 미러일 뿐 권위 있는 입력이 아니다([/decisions/reproducibility.md](/decisions/reproducibility.md)의
  3층 pin이 진짜 권위). `pipeline/<id>/`의 중간산출물도 스크립트가 처음부터 다시 만들어낼 수
  있어야 하며, "숨은 입력"이 되면 안 된다.
- **경로 노출은 env var로**: 컨테이너 안 스크립트는 host 절대경로를 몰라도 되게, `run.py`가
  `UV_CACHE_DIR`(uv가 직접 읽음), `GEOVARS_CACHE_ROOT`, `GEOVARS_R2_CACHE_DIR`,
  `GEOVARS_DUCKDB_CACHE_DIR`, `GEOVARS_SCRATCH_DIR`(collection별)를 주입하고,
  `geovars.pipeline`이 이를 읽는 헬퍼(`cache_root()`/`r2_cache_dir()`/`duckdb_cache_dir()`/
  `scratch_dir()`)를 제공한다.
- **collection별 격리**: `pipeline/<collection-id>/`는 `run.py`가 이미 아는 `collection_id`로
  자동 분리되어 스크립트끼리 스크래치를 오염시키지 않는다.
- `process/` 대신 `pipeline/`을 하위 이름으로 택함 — `pipeline/` 워크스페이스 소유라는 게
  이름에서 바로 드러남.

## 공용 유틸 — geovars 단일 패키지

- 스크립트는 공용 유틸을 **버전 고정으로 소비**해야 옛 스크립트 재현성이 안 깨진다.
  → PEP 723에서 `geovars`를 **git commit으로 pin**(예: `geovars @ git+<repo>@<commit>`).
  운영이 안정되면 semver **git 태그**로 전환.
- `geovars`는 **단일 패키지 + optional extras 엄격 분리**: marimo 기반 STAC 대시보드,
  파이프라인 유틸, STAC 카탈로그 검색, 팀 변수생성·모델링. 코어는 지연 임포트, 각 기능은
  자기 extra만 — 스크립트가 `geovars[pipeline]`을 끌 때 대시보드·모델링 deps가 안 딸려오게.
  (분리가 실제로 아프면 그때 안정 코어를 별 패키지로 떼어냄.)

## 미해결

- 이미지 레지스트리 선택(GHCR / R2 등)과 보존 운영. 정해지기 전까지 `pipeline/run.py`는
  로컬에 이미지가 없으면 `pipeline/images/<image>/`에서 직접 빌드하는 것으로 폴백한다(위
  "CLI 계약과 컨테이너 실행 구현" 참고).
- provenance schema(이미지 digest·lock·입출력 manifest)의 정확한 필드명, R2 업로드·STAC
  발행의 staging·복구 절차, 재현 원커맨드 — 구현 시점에 정하고 사후 포착.

CI는 도입하지 않기로 확정했으므로
([/decisions/reproducibility.md](/decisions/reproducibility.md)), lock 커밋·catalog
정합성 등의 자동 게이트는 이 목록에서 제외한다 — 미해결이 아니라 **안 하기로 결정**됐다.

## 관련

- [/decisions/reproducibility.md](/decisions/reproducibility.md)
- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)
- [/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)
