---
type: decision
title: 파이프라인 아키텍처 — 처리 스크립트·환경·실행
description: 모노레포 구조, 자기완결 처리 스크립트(PEP723+lock), Docker+pixi로 시스템 환경 고정, Python 래퍼 실행, geovars 단일 패키지. 버전 재현은 flat 스크립트 + git commit provenance.
tags: [pipeline, monorepo, pixi, docker, pep723, uv, reproducibility, geovars]
timestamp: 2026-07-21
---

# 파이프라인 아키텍처 — 처리 스크립트·환경·실행

옛 refactoring-plan에서 처리 스크립트·의존성·Docker·공용 유틸 전반을 물려받았지만, 이 프로젝트에서 재합의된 적은 없었다.
이를 백지에서 다시 논의해 확정한 기록이다.

## 모노레포 구조

```
geovars/                       # geovars 컴포넌트 (자기완결)
  pyproject.toml               #   패키지 정의 + optional extras
  geovars/                     #   임포트 패키지 (대시보드·파이프라인 유틸·카탈로그 검색·모델링)
pipeline/                      # 처리 실행 워크스페이스
  run.py                       #   실행기: image 해석 → 컨테이너 → lock → uv run
  images/<YYYY.MM.DD>/         #   시스템 환경 정의: pixi.toml + pixi.lock + Dockerfile
  process/<collection-id>.py   #   flat 처리 스크립트 (+ <collection-id>.py.lock)
stac-metadata/                 # STAC JSON, 데이터 사실의 유일한 권위 있는 기준. 버전 차원은 여기
knowledge/                     # OKF 지식
.claude/                       # 에이전트 skills
.gitignore  CLAUDE.md  README.md
```

- **컴포넌트 자기완결**: 각 최상위 디렉토리는 동급 컴포넌트다.
  - Python 패키징 설정은 레포 루트가 아니라 `geovars/`가 소유한다(`geovars/pyproject.toml`).
  - 임포트 패키지는 `geovars/geovars/`에 둔다.
  - src-layout 대신 한 겹 중첩 구조를 쓴다.
  - 루트는 "레포=패키지"가 아니라 모노레포다.
- **실행 소유권**: 처리 스크립트를 실행하는 책임은 `pipeline/` 워크스페이스에 있다.
  - 실행기는 `pipeline/run.py`이다.
  - geovars 패키지의 콘솔 명령이 아니다.

## 처리 스크립트 모델

- **자기완결 단일 파일**: 스크립트마다 PEP 723 인라인 의존성 선언과 스크립트별 lock을 갖고 `uv run --script`로 실행한다.
  - 옛 스크립트를 건드리지 않고 새 스크립트에서 최신 라이브러리를 채택할 수 있다.
  - 기각한 대안은 단일 공용 환경과 editable 로컬 참조다.
  - editable 로컬 참조는 옛 스크립트가 최신 유틸을 써서 재현성을 깨뜨린다.
- **flat 레이아웃**: `pipeline/process/<collection-id>.py`.
  - 파일명이 곧 collection id다.
- 버전 차원은 스크립트가 아니라 `stac-metadata/`에 둔다.
  - `pipeline/process/`는 flat 구조로 최신 스크립트만 담는다.
- **버전 재현은 git commit 기반**이다.
  - 각 발행 버전의 STAC provenance에 그 버전을 생성한 git commit과 `image` 버전을 기록한다.
  - 재현은 그 commit을 checkout해 그때의 스크립트와 lock을 복원하고, 보존된 image를 pull해 실행하는 순서로 이뤄진다.
  - 기각한 대안은 버전별 스크립트 디렉토리(`version=<v>/`)다.
    - 유틸과 image도 그 시점 것이어야 하므로 commit provenance는 어차피 필요하다.
    - 그래서 스크립트 복사본을 따로 두는 건 중복이다.
    - flat 구조에 commit provenance를 더하는 쪽이 더 단순하다.
  - 감수한 트레이드오프가 있다.
    - HEAD에서 모든 버전의 스크립트를 나란히 보는 편의는 포기한다.
    - 대신 단순성과, commit pin 하나로 재현 메커니즘을 통일하는 이점을 택했다.
- **lock 파일은 스크립트와 같은 디렉터리에 둔다**(`<collection-id>.py.lock`).
  - `pipeline/process.lock/`처럼 별도 경로로 분리하는 안도 검토했다.
  - 하지만 uv가 스크립트 lock의 저장 위치를 전혀 지정할 수 없다는 점을 확인했다.
  - `uv lock --script`와 `uv run --script` 모두 `<script>.lock`을 스크립트 바로 옆에 고정하고, 관련 플래그나 환경변수가 없다.
  - `uv --version` 0.10.11 기준으로 확인했다.
  - `run.py`가 매번 복사·이동으로 흉내 내는 방법도 검토했지만, 복잡도 대비 이득이 낮아 기각했다.
  - 파일 트리가 번잡해 보이는 문제는 에디터의 File Nesting 설정으로 해결한다.
  - 예를 들어 VSCode의 `explorer.fileNesting.patterns`로 `*.py.lock`을 같은 이름의 `.py` 아래로 접을 수 있다.

`pipeline/process/<collection-id>.py`는 함수 나열이 아니라 `Processor` 클래스 하나로 쓰는 것을 공식 템플릿으로 확정했다.
첫 실사용은 [/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md)다.
사유는 향후 처리 단계 간 상태 공유와 가독성이다.

```python
class Processor:
    COLLECTION_ID = "..."   # = 파일명 = collection id
    VERSION = "0.1.0"
    TITLE = "..."
    DESCRIPTION = "..."
    # 그 외 collection 고유 설정·하드코딩 데이터도 클래스 변수로

    def build_...(self) -> ...:
        ...  # 처리 단계 하나당 메서드 하나

    def run(self) -> None:
        ...  # 단계 메서드들을 순서대로 호출하는 오케스트레이터


if __name__ == "__main__":
    Processor().run()
```

- PEP723 의존성은 정확한 버전(`==`)으로 고정한다.
  - 예를 들어 `duckdb==1.5.4`처럼 쓴다.
  - lock 파일이 전이 의존성까지 이미 고정하므로 정보로서는 중복이지만, 헤더만 봐도 재현 버전을 바로 알 수 있는 명시성을 우선한다.
  - 재현성을 보장하는 것은 lock이며, 이 사실은 앞으로도 변하지 않는다.

## 시스템 환경 — Docker + pixi (장기 보존)

- 두 층으로 분리한다.
  - Docker가 바깥 층으로 OS 층까지 고정하고, pixi가 안쪽 층으로 conda-forge에서 GDAL/GEOS/PROJ/uv를 `pixi.lock`으로 고정한다.
  - "pixi로 만든 환경을 담은 Docker 컨테이너"인 셈이다.
- **장기 보존을 위해 빌드된 이미지를 레지스트리에 보존한다.**
  - 냉동 상태로 두는 것으로, 데이터 삭제 금지 정책을 이미지에도 적용한 것이다.
  - 10년 후 재현에서 가장 튼튼한 경로는 "레시피 rebuild"가 아니라 "얼려둔 OCI 이미지 pull"이다.
  - 빌드 정의(`Dockerfile`과 `pixi.lock`)도 레포에 커밋해 rebuild도 가능하게 둔다.
- `pipeline/images/<YYYY.MM.DD>/`는 `pixi.toml`과 `pixi.lock`, `Dockerfile`로 구성되는 빌드 정의다.
  - 식별자는 `YYYY.MM.DD`이고, 같은 날 두 번 갱신하면 `-2` 접미사를 붙인다.
- 스크립트는 자기 시스템 환경을 PEP 723 블록 안 전용 테이블로 pin한다.

  ```python
  # /// script
  # dependencies = ["duckdb", "pyproj"]
  #
  # [tool.geovars]
  # image = "2026.07.20"        # → pipeline/images/2026.07.20/
  # ///
  ```

  - 시스템 의존성을 올리면 새 `images/<날짜>/`를 만든다.
  - 옛 스크립트는 계속 옛 `image`를 가리킨다.
  - [/decisions/reproducibility.md](/decisions/reproducibility.md)에서 말하는 시스템 층 pin이다.
- **단일 정규 arch로 `linux/arm64`를 쓴다.**
  - 한 arch를 쓰면 결정론적 출력을 얻는다.
  - 이 성질은 어떤 arch를 고르든 유지된다.
  - 팀이 주로 Apple Silicon Mac에서 작업하므로, 그 환경에서 에뮬레이션 없이 네이티브로 빌드·실행되는 쪽을 정규로 택했다.
  - x86_64 호스트, 예를 들어 인텔 맥이나 클라우드 러너에서는 반대로 에뮬레이션이 필요해진다.
  - CI를 안 쓰기로 확정했으므로 이 비용은 주로 사람이 드물게 x86_64에서 빌드·실행할 때만 발생한다.
  - 대량 처리 속도나 팀 구성이 바뀌면, 예를 들어 x86_64 비중이 늘어나면 재검토한다.
  - 기각한 대안은 multi-arch, `linux/amd64` 유지, plain Dockerfile+apt, pixi-only 네 가지다.
    - multi-arch는 cross-arch 부동소수점·SIMD 출력 차이 위험이 있다.
    - 같은 스크립트가 arch에 따라 다른 결과를 낼 수 있다.
    - `linux/amd64` 유지는 팀이 쓰는 환경인 Apple Silicon과 안 맞아 매 빌드·실행에서 불필요한 에뮬레이션 비용을 부담한다.
    - plain Dockerfile+apt는 apt 미러가 옛 버전을 지워 rebuild가 불가능해진다.
    - pixi-only는 OS 층을 고정하지 못하고 pixi가 신생 도구라는 리스크를 안는다.
- `pixi.toml`은 `platforms = ["linux-aarch64"]`를 쓴다.
  - conda-forge에서 리눅스 ARM64를 가리키는 이름이다.
  - `dependencies`에는 `python=3.12.*`, `gdal>=3.13,<4`, `geos>=3.14,<4`, `proj>=9.8,<10`, `uv>=0.11,<0.12`를 둔다.
  - 2026-07-21 시점 conda-forge에서 최신으로 solve한 결과이며, amd64에서 `pixi add`했을 때와 완전히 동일한 버전이 aarch64에서도 solve됨을 확인했다.
  - 향후 스크립트가 필요로 하는 라이브러리가 늘면 이 최초 이미지에 추가하거나, 필요하면 새 날짜 디렉토리를 만든다.
- `pixi.lock` 생성은 `pixi lock`만으로 충분하다.
  - 설치 없이 solve만 하므로, 개발자가 x86_64 머신에서 작업해도 `linux-aarch64` lock을 문제없이 만들 수 있고 반대 방향도 마찬가지다.
  - 에뮬레이션은 실제 `docker build`나 `docker run` 시점에, 그것도 실행 host arch와 이미지 arch가 다를 때만 필요하다.
- `Dockerfile`은 2-stage로 구성한다.
  1. build 스테이지에서 공식 설치 스크립트(`curl -fsSL https://pixi.sh/install.sh | sh`)로 pixi 자체를 설치하고 `pixi install --locked`를 실행한다.
     - 기각한 대안은 `ghcr.io/prefix-dev/pixi` 사전빌드 베이스 이미지다.
     - 정확한 태그가 존재하고 유지되는지 확인 없이 고정하는 리스크를 피하려고 설치 스크립트 방식을 택했다.
     - 설치 스크립트는 실행 중인 arch를 자동 감지해 맞는 pixi 바이너리를 받으므로 이 줄은 그대로 둔다.
  2. 최종 스테이지는 build 스테이지에서 만들어진 `.pixi/envs/default`만 복사해 런타임 이미지를 가볍게 유지한다.
     - pixi 자체와 빌드 캐시는 최종 이미지에 남지 않는다.
  - 모든 `FROM`에 `--platform=linux/arm64`를 명시적으로 지정해, x86_64 호스트에서 빌드해도 항상 정규 arch(linux/arm64)로 고정되게 했다.
    - 위 "단일 정규 arch" 결정과 일치한다.
  - pixi 버전은 `pixi.lock`을 만든 버전(`v0.65.0`)으로 install 스크립트에 명시 고정한다.
    - "latest"로 두면 컨테이너 안 pixi가 더 최신 lock 포맷(v7 등)을 요구해 불필요한 재-lock을 유발할 수 있다는 사실을 확인했다.
    - 최초 빌드 시 `PIXI_VERSION`을 지정하지 않았더니 v7 업그레이드 경고가 발생했고, 버전을 고정한 뒤 재현됐다.
  - Apple Silicon Mac(호스트=arm64)에서 `docker build --platform linux/arm64` 후 `docker run`으로 네이티브 정상 동작을 검증했다.
    - `uname -m`은 `aarch64`이고 에뮬레이션 경고가 없다.
    - `gdalinfo --version`은 GDAL 3.13.1이다.
    - `python3 --version`은 3.12.13이다.
    - `uv --version`은 0.11.29이고 `aarch64-unknown-linux-gnu` 빌드다.

## 실행 — pipeline/ 워크스페이스의 실행기 (크로스플랫폼)

- 처리 스크립트 실행은 **`pipeline/` 워크스페이스의 책임**이다.
  - 실행기 `pipeline/run.py`는 Python으로 짠 stdlib 부트스트랩이며, Windows·Mac·Linux에서 동일하게 실행된다.
  - `.sh`는 Windows에서 네이티브로 돌지 않아 기각했다.
  - geovars 패키지의 콘솔 명령으로 두는 방식도 기각했다.
  - 실행은 파이프라인 관심사지 라이브러리 관심사가 아니다.
  - 컨테이너 없이도 도는 얇은 부트스트랩으로 순환 의존 문제를 피한다.
- 실행기는 한 번 실행에 세 단계를 거친다.
  - 스크립트 상단의 `image`를 읽어 그 컨테이너로 진입하고, lock을 처리한 뒤, `uv run --script`를 실행한다.
- **CLI**는 `python pipeline/run.py <collection-id> [--relock]`다.
  - `argparse` 기반이고, `--relock`이 없으면 기존 lock을 그대로 쓰고, lock 파일 자체가 없으면 새로 생성한다.
  - 아래 lock 동작 규칙 그대로다.
- **컨테이너 진입**은 레포 전체를 `/workspace`로 bind mount한다(`-w /workspace`).
  - 스크립트를 이미지 안에 굽지 않으므로, `pipeline/process/<id>.py`를 고치고 다시 실행하면 이미지 재빌드 없이 바로 반영된다.
- **이미지 확보**는 `docker image inspect`로 로컬에 있는지 먼저 확인하고, 있으면 그대로 쓴다.
  - 매 실행마다 빌드나 pull을 하지 않는다.
  - 이미지 빌드는 `pipeline/images/<날짜>/` 버전이 바뀔 때만 드물게 일어난다.
  - 로컬에 없으면 `pipeline/images/<image>/`에서 로컬 빌드로 폴백한다.
  - "보존된 이미지 pull"이 정규 경로지만, 레지스트리 선택이 아직 미해결이라 그게 정해지기 전까지의 임시 경로다.
- **lock 처리는 별도 컨테이너 실행으로 분리한다.**
  - GENERATE나 RELOCK이면 먼저 `uv lock --script`를 한 번 실행하고, 끝나면 커밋하라는 안내를 출력한다.
  - 그다음 항상 `uv run --frozen --script`로 실행한다.
  - FROZEN이 가장 흔한 반복 실행 경로이며, 이 경우 컨테이너 실행이 한 번뿐이다.
- **lock 동작 규칙**: 없으면 컨테이너 안에서 생성하고, 있으면 frozen 그대로 사용하고, 재-lock은 명시적 플래그(`--relock`)로만 한다.
  - 매 실행 자동 재생성은 금지한다.
  - pin이 무효화되기 때문이다.
  - 재-lock은 의존성을 의도적으로 바꾸는 것이므로, 산출물이 발행됐다면 새 버전으로 취급한다.
- **smoketest로 실행 경로를 검증했다.**
  - 임시 PEP 723 스크립트로 `python pipeline/run.py <id>`의 전 경로를 돌려 확인했다.
  - 이미지 로컬 빌드 폴백에서 lock 생성, 실행까지, 그리고 재실행 시 FROZEN 경로까지 포함한다.
- **lock 커밋은 필수 규칙이다.**
  - CI는 도입하지 않기로 확정했으므로 커밋 여부를 확인하는 자동 게이트는 없다.
  - 위반은 사후 발견에 의존한다.
  - 자세한 내용은 [/decisions/reproducibility.md](/decisions/reproducibility.md)에 있다.

## 캐시 — `.cache/`

빠른 수정과 재실행을 반복하는 작업 흐름의 병목을 없애기 위해 도구별 캐시를 레포 루트 `.cache/`(git-ignored) 밑에 모으고, 컨테이너엔 통째로 `/cache`로 한 번만 mount한다.

```
.cache/
  uv/                       # uv wheel/venv 캐시 (UV_CACHE_DIR)
  duckdb/                   # duckdb extension·spill(temp_directory)
  s3/                       # S3 호환 오브젝트 스토리지(현재 Cloudflare R2)의 로컬 미러(양방향)
  pipeline/<collection-id>/ # 스크립트별 중간산출물·스크래치
```

- **불변식 — 캐시는 순수 가속 장치이지 입력이 아니다.**
  - `.cache/`를 통째로 지워도 재실행하면 같은 결과가 나와야 한다.
  - 느려질 뿐이다.
  - `s3/`는 이미 스토리지에 박제되고 STAC `file:checksum`으로 고정된 원본의 로컬 미러일 뿐, 권위 있는 입력이 아니다.
  - 진짜 권위는 [/decisions/reproducibility.md](/decisions/reproducibility.md)에서 말하는 3층 pin이다.
  - `pipeline/<id>/`의 중간산출물도 스크립트가 처음부터 다시 만들어낼 수 있어야 하며, "숨은 입력"이 되면 안 된다.
- **`s3/`는 양방향 미러다.**
  - 다운로드 read-through 미러였던 원래 개념에 업로드 전 준비 단계도 같은 자리로 통합했다.
  - 처리 스크립트가 산출물을 실제 S3 key와 동일한 상대경로(`.cache/s3/<key>`)에 직접 쓰고, 그 파일을 그대로 업로드한다(`geovars.pipeline.s3_cache_path(key)`/`upload_asset(key)`).
  - `.cache/s3/`가 버킷 네임스페이스를 그대로 반영하는 로컬 미러라는 하나의 개념으로 통일해, 별도 `pipeline/<id>/` 스크래치 경로와 실제 버킷 key 사이의 매핑을 스크립트가 따로 관리할 필요를 없앴다.
  - 첫 실사용은 [/decisions/geovars-references-collection.md](/decisions/geovars-references-collection.md)다.
- **경로 노출은 환경변수로 한다.**
  - 컨테이너 안 스크립트는 host 절대경로를 몰라도 되도록, `run.py`가 `UV_CACHE_DIR`(uv가 직접 읽음), `GEOVARS_CACHE_ROOT`, `GEOVARS_S3_CACHE_DIR`, `GEOVARS_DUCKDB_CACHE_DIR`, `GEOVARS_SCRATCH_DIR`(collection별)를 주입한다.
  - `geovars.pipeline`이 이를 읽는 헬퍼(`cache_root()`/`s3_cache_dir()`/`duckdb_cache_dir()`/`scratch_dir()`)를 제공한다.
  - 변수명은 스토리지 벤더 중립(`S3`)으로 택했다.
  - 오브젝트 스토리지 자체는 현재 Cloudflare R2이지만, 자격증명과 엔드포인트 구성이 S3 호환 API로 동일해 후임자가 다른 S3 호환 스토리지로 갈아탈 가능성을 이름에서부터 열어둔다.
  - Cloudflare R2 채택 근거는 [/decisions/infrastructure.md](/decisions/infrastructure.md)에 있고, 벤더 중립 네이밍 근거는 [/decisions/secrets-and-s3-client.md](/decisions/secrets-and-s3-client.md)에 있다.
- **collection별로 격리한다.**
  - `pipeline/<collection-id>/`는 `run.py`가 이미 아는 `collection_id`로 자동 분리되어 스크립트끼리 스크래치를 오염시키지 않는다.
- `process/` 대신 `pipeline/`을 하위 이름으로 택했다.
  - `pipeline/` 워크스페이스 소유라는 게 이름에서 바로 드러난다.

## 공용 유틸 — geovars 단일 패키지

- 스크립트는 공용 유틸을 버전 고정으로 소비해야 옛 스크립트의 재현성이 깨지지 않는다.
  - PEP 723에서 `geovars`를 git commit으로 pin한다(예: `geovars @ git+<repo>@<commit>`).
  - 운영이 안정되면 semver git 태그로 전환한다.
- `geovars`는 단일 패키지에 optional extras를 엄격히 분리한 구조다.
  - marimo 기반 STAC 대시보드, 파이프라인 유틸, STAC 카탈로그 검색, 팀 변수 생성·모델링을 담는다.
  - 코어는 지연 임포트로 두고, 각 기능은 자기 extra만 갖는다.
  - 스크립트가 `geovars[pipeline]`을 끌어올 때 대시보드나 모델링 의존성이 딸려오지 않게 하기 위해서다.
  - 분리가 아프면 그때 안정 코어를 별 패키지로 떼어낸다.
- 레포에 `origin`(`github.com/ncc-airhealth/geovars`)이 이미 있지만, 아직 push 안 한 로컬 커밋도 즉시 pin해 반복 개발할 수 있어야 해서 `geovars[pipeline,catalog] @ git+file:///workspace@<commit>#subdirectory=geovars`를 쓴다.
  - 컨테이너 bind mount로 이미 보이는 로컬 레포를 `git+file://`로 참조하는 것이다.
  - 실제 GitHub 호스팅 pin(`git+https://github.com/...@<commit>`)은 push 이후 별도 검증이 필요하며, 미해결로 남아 있다.
- uv가 `git+` 의존성을 resolve하려면 `git` 실행파일이 필요하므로, `pipeline/images/2026.07.21/Dockerfile` 최종 스테이지에 `git` 패키지를 추가했다.
- 스크립트를 고쳐 geovars 쪽 pin 커밋 해시가 바뀌면 `--relock`이 필요하다.
  - 의존성 변경은 재-lock 대상이며, 위 lock 동작 규칙 그대로다.

## 미해결

- 이미지 레지스트리 선택(GHCR나 R2 등)과 보존 운영이 아직 안 정해졌다.
  - 정해지기 전까지 `pipeline/run.py`는 로컬에 이미지가 없으면 `pipeline/images/<image>/`에서 직접 빌드하는 것으로 폴백한다.
  - 위 "실행" 섹션을 참고한다.
- provenance schema, 즉 이미지 digest·lock·입출력 manifest의 정확한 필드명, R2 업로드와 STAC 발행의 준비 단계·복구 절차, 재현 원커맨드는 구현 시점에 정하고 사후 포착한다.
- `geovars`를 실제 GitHub 호스팅 커밋(`git+https://github.com/ncc-airhealth/geovars.git@<commit>`)으로 pin하는 경로는 아직 미검증이다.
  - 지금은 `git+file:///workspace@<commit>`, 즉 로컬 pin만 확인됐다.
  - 위 "공용 유틸 — geovars 단일 패키지" 섹션을 참고한다.
  - push 이후 검증이 필요하다.

CI는 도입하지 않기로 확정했다. 근거는 [/decisions/reproducibility.md](/decisions/reproducibility.md)에 있다.
그래서 lock 커밋과 catalog 정합성 같은 자동 게이트는 이 목록에서 제외한다. 미해결이 아니라 안 하기로 결정된 것이다.

## 관련

- [/decisions/reproducibility.md](/decisions/reproducibility.md)
- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md)
- [/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md)
