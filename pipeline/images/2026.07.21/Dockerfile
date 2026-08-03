# 시스템 환경(빌드 정의): GDAL/GEOS/PROJ/uv 버전은 이 디렉토리의 pixi.lock에 고정된다.
# 정규 arch는 linux/arm64 — 팀이 주로 Apple Silicon Mac에서 작업해 네이티브 실행을 우선함.
# arch 강제는 Dockerfile FROM --platform 상수가 아니라 pipeline/run.py 의
# `docker build|run --platform` (CANONICAL_PLATFORM) 이 담당한다.
# (FROM --platform=linux/arm64 상수는 BuildKit FromPlatformFlagConstDisallowed 경고를 낸다.)
# x86_64 호스트에서는 그 CLI 플래그로 에뮬레이션 arm64 가 강제된다.
# 세부: ../../../.agents/skills/pipeline-script-shape/SKILL.md

FROM ubuntu:24.04 AS build
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*
# pixi 버전을 pixi.lock을 만든 버전과 맞춰 고정 — "latest"로 두면 이후 빌드에서 다른 lock
# 포맷/solver로 재현성이 흔들릴 수 있다.
RUN curl -fsSL https://pixi.sh/install.sh | PIXI_VERSION=v0.65.0 PIXI_NO_PATH_UPDATE=1 sh
ENV PATH="/root/.pixi/bin:${PATH}"

WORKDIR /image
COPY pixi.toml pixi.lock ./
RUN pixi install --locked

FROM ubuntu:24.04
# git: uv가 `git+...` 의존성(ardkr 패키지의 commit pin)을 resolve하려면 필요하다.
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /image
COPY --from=build /image/.pixi/envs/default /image/.pixi/envs/default
ENV PATH="/image/.pixi/envs/default/bin:${PATH}"
WORKDIR /workspace
