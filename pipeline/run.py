"""처리 스크립트 실행 부트스트랩.

  래퍼 한 번 실행 =
    ① 스크립트 상단 PEP 723 `[tool.ardkr] image` 읽기 → 그 컨테이너 진입
    ② lock 처리 (없으면 생성 / 있으면 frozen / --relock 로만 재생성)
    ③ 컨테이너 안에서 `uv run --script <script>`

CLI: `python3 pipeline/run.py <collection-id>`

캐시(`.cache/`)는 순수 가속 장치다 — 지워도 스크립트는 처음부터 다시 돌아 같은 결과를
내야 한다(재현성은 3층 pin이 보장).
"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# 정규 arch. 세부: pipeline/images/README.md.
CANONICAL_PLATFORM = "linux/arm64"

# 컨테이너 안 경로 상수.
CONTAINER_WORKSPACE = "/workspace"
CONTAINER_CACHE_ROOT = "/cache"
CONTAINER_CATALOG_ROOT = f"{CONTAINER_WORKSPACE}/catalog"


class LockAction(Enum):
    GENERATE = "generate"  # lock 없음 → 컨테이너 안에서 생성
    FROZEN = "frozen"      # lock 있음 → 그대로 사용(pin 유지)
    RELOCK = "relock"      # --relock → 재생성(새 버전 취급)


@dataclass(frozen=True)
class RunPlan:
    collection_id: str
    root: Path          # 레포 루트
    script: Path        # pipeline/process/<collection-id>.py
    lock: Path          # pipeline/process/<collection-id>.py.lock
    image: str          # YYYY.MM.DD
    image_dir: Path     # pipeline/images/<image>/
    lock_action: LockAction


@dataclass(frozen=True)
class CachePaths:
    root: Path  # <repo>/.cache/
    collection_id: str


def find_repo_root(start: Path | None = None) -> Path:
    """.git + pipeline/ 를 가진 레포 루트를 위로 탐색."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists() and (candidate / "pipeline").is_dir():
            return candidate
    raise FileNotFoundError(
        "레포 루트를 찾지 못했습니다(.git + pipeline/ 이 있는 디렉토리). "
        "레포 안에서 실행하세요."
    )


def _read_image(script: Path) -> str:
    """PEP 723 인라인 메타데이터에서 [tool.ardkr] image 를 읽는다."""
    text = script.read_text(encoding="utf-8")
    block = _extract_pep723(text)
    if block is None:
        raise ValueError(f"{script} 에 PEP 723 스크립트 블록(`# /// script`)이 없습니다.")
    meta = tomllib.loads(block)
    try:
        image = meta["tool"]["ardkr"]["image"]
    except KeyError as exc:
        raise ValueError(
            f"{script} 의 PEP 723 블록에 [tool.ardkr] image 가 없습니다."
        ) from exc
    if not isinstance(image, str) or not image:
        raise ValueError(f"{script} 의 image 값이 비었거나 문자열이 아닙니다: {image!r}")
    return image


def _extract_pep723(text: str) -> str | None:
    """`# /// script` … `# ///` 사이의 주석 본문을 TOML 문자열로 복원한다.

    PEP 723 규격: 각 줄은 `# ` 또는 `#` 로 시작하며 그 접두를 벗겨 TOML 로 파싱한다.
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "# /// script":
            start = i + 1
            break
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped == "# ///":
            return "\n".join(body)
        if stripped == "#":
            body.append("")
        elif line.startswith("# "):
            body.append(line[2:])
        elif line.startswith("#"):
            body.append(line[1:])
        else:
            # 블록이 닫히기 전 비주석 줄 → 형식 오류
            return None
    return None  # 닫는 `# ///` 없음


def plan_run(collection_id: str, *, relock: bool, repo_root: Path | None = None) -> RunPlan:
    root = repo_root or find_repo_root()
    script = root / "pipeline" / "process" / f"{collection_id}.py"
    if not script.is_file():
        raise FileNotFoundError(f"처리 스크립트가 없습니다: {script}")

    image = _read_image(script)
    image_dir = root / "pipeline" / "images" / image
    if not image_dir.is_dir():
        raise FileNotFoundError(
            f"스크립트가 가리키는 image 정의가 없습니다: {image_dir} "
            f"(pipeline/images/<YYYY.MM.DD>/ 에 pixi.toml+pixi.lock+Dockerfile)"
        )

    lock = script.with_suffix(".py.lock")
    if relock:
        action = LockAction.RELOCK
    elif lock.is_file():
        action = LockAction.FROZEN
    else:
        action = LockAction.GENERATE

    return RunPlan(
        collection_id=collection_id,
        root=root,
        script=script,
        lock=lock,
        image=image,
        image_dir=image_dir,
        lock_action=action,
    )


def image_tag(image: str) -> str:
    return f"ardkr-pipeline-image:{image}"


def ensure_image(plan: RunPlan) -> str:
    """이미지가 로컬에 있으면 그대로 쓰고, 없으면 빌드한다.

    레지스트리 선택(GHCR/R2 등)은 아직 미정이라, 정규 경로인 "보존된 이미지 pull"은
    나중에 여기 추가한다. 지금은 로컬 빌드로 폴백한다 — 매 스크립트 실행마다가 아니라
    이미지가 없을 때 딱 한 번만 든다.
    """
    tag = image_tag(plan.image)
    inspect = subprocess.run(
        ["docker", "image", "inspect", tag],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if inspect.returncode == 0:
        return tag

    subprocess.run(
        ["docker", "build", "--platform", CANONICAL_PLATFORM, "-t", tag, str(plan.image_dir)],
        check=True,
    )
    return tag


def prepare_cache(root: Path, collection_id: str) -> CachePaths:
    """`.cache/` 서브디렉토리를 만든다(host 전용, git-ignored, 순수 가속 장치)."""
    cache_root = root / ".cache"
    for sub in ("uv", "duckdb", "s3", f"pipeline/{collection_id}"):
        (cache_root / sub).mkdir(parents=True, exist_ok=True)
    return CachePaths(root=cache_root, collection_id=collection_id)


def _to_container_path(root: Path, path: Path) -> str:
    return f"{CONTAINER_WORKSPACE}/{path.relative_to(root).as_posix()}"


def _docker_run(root: Path, image_ref: str, cache: CachePaths, inner_argv: list[str]) -> int:
    argv = [
        "docker", "run", "--rm",
        "--platform", CANONICAL_PLATFORM,
        "-v", f"{root}:{CONTAINER_WORKSPACE}",
        "-w", CONTAINER_WORKSPACE,
        "-v", f"{cache.root}:{CONTAINER_CACHE_ROOT}",
    ]
    # 레포 루트 .env → 컨테이너 환경변수. 캐시 경로 -e 가 뒤에 와서 덮어쓴다.
    env_file = root / ".env"
    if env_file.is_file():
        argv.extend(["--env-file", str(env_file)])
    argv.extend([
        "-e", f"UV_CACHE_DIR={CONTAINER_CACHE_ROOT}/uv",
        "-e", f"ARDKR_CACHE_ROOT={CONTAINER_CACHE_ROOT}",
        "-e", f"ARDKR_S3_CACHE_DIR={CONTAINER_CACHE_ROOT}/s3",
        "-e", f"ARDKR_DUCKDB_CACHE_DIR={CONTAINER_CACHE_ROOT}/duckdb",
        "-e", f"ARDKR_SCRATCH_DIR={CONTAINER_CACHE_ROOT}/pipeline/{cache.collection_id}",
        "-e", f"ARDKR_CATALOG_ROOT={CONTAINER_CATALOG_ROOT}",
        image_ref,
        *inner_argv,
    ])
    return subprocess.run(argv).returncode


def run_collection(collection_id: str, *, relock: bool = False) -> int:
    plan = plan_run(collection_id, relock=relock)

    tag = ensure_image(plan)
    cache = prepare_cache(plan.root, collection_id)
    container_script = _to_container_path(plan.root, plan.script)

    if plan.lock_action in (LockAction.GENERATE, LockAction.RELOCK):
        rc = _docker_run(plan.root, tag, cache, ["uv", "lock", "--script", container_script])
        if rc != 0:
            return rc

    return _docker_run(plan.root, tag, cache, ["uv", "run", "--frozen", "--script", container_script])


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("collection_id", help="pipeline/process/<collection-id>.py 의 id")
    parser.add_argument(
        "--relock", action="store_true", help="lock을 의도적으로 재생성(새 버전 취급)"
    )
    args = parser.parse_args(argv)
    return run_collection(args.collection_id, relock=args.relock)


if __name__ == "__main__":
    sys.exit(main())
