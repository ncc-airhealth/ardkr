"""처리 스크립트 실행 부트스트랩.

확정된 알고리즘(knowledge/decisions/pipeline-architecture.md):

  래퍼 한 번 실행 =
    ① 스크립트 상단 PEP 723 `[tool.geovars] image` 읽기 → 그 컨테이너 진입
    ② lock 처리 (없으면 생성 / 있으면 frozen / --relock 로만 재생성)
    ③ 컨테이너 안에서 `uv run --script <script>`

경로·image 해석과 lock 상태 판정은 여기서 실제로 수행한다. 컨테이너 진입·실행
(docker run linux/amd64 …)은 문서상 아직 '미해결'이라 여기선 뼈대만 두고 TODO 로 남긴다.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class LockAction(Enum):
    GENERATE = "generate"  # lock 없음 → 컨테이너 안에서 생성
    FROZEN = "frozen"      # lock 있음 → 그대로 사용(pin 유지)
    RELOCK = "relock"      # --relock → 재생성(새 버전 취급)


@dataclass(frozen=True)
class RunPlan:
    collection_id: str
    script: Path        # pipeline/process/<collection-id>.py
    lock: Path          # pipeline/process/<collection-id>.py.lock
    image: str          # YYYY.MM.DD
    image_dir: Path     # pipeline/images/<image>/
    lock_action: LockAction


def find_repo_root(start: Path | None = None) -> Path:
    """CLAUDE.md + pipeline/ 를 가진 레포 루트를 위로 탐색."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "CLAUDE.md").is_file() and (candidate / "pipeline").is_dir():
            return candidate
    raise FileNotFoundError(
        "레포 루트를 찾지 못했습니다(CLAUDE.md + pipeline/ 이 있는 디렉토리). "
        "레포 안에서 실행하세요."
    )


def _read_image(script: Path) -> str:
    """PEP 723 인라인 메타데이터에서 [tool.geovars] image 를 읽는다."""
    text = script.read_text(encoding="utf-8")
    block = _extract_pep723(text)
    if block is None:
        raise ValueError(f"{script} 에 PEP 723 스크립트 블록(`# /// script`)이 없습니다.")
    meta = tomllib.loads(block)
    try:
        image = meta["tool"]["geovars"]["image"]
    except KeyError as exc:
        raise ValueError(
            f"{script} 의 PEP 723 블록에 [tool.geovars] image 가 없습니다."
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
        script=script,
        lock=lock,
        image=image,
        image_dir=image_dir,
        lock_action=action,
    )


def run_collection(collection_id: str, *, relock: bool = False) -> int:
    plan = plan_run(collection_id, relock=relock)
    print(f"[geovars] collection : {plan.collection_id}")
    print(f"[geovars] script     : {plan.script}")
    print(f"[geovars] image      : {plan.image} ({plan.image_dir})")
    print(f"[geovars] lock        : {plan.lock_action.value} ({plan.lock})")

    # TODO(미해결): 컨테이너 진입·실행. 확정 알고리즘은 아래와 같다.
    #   1) pipeline/images/<image>/ 로부터 linux/amd64 이미지를 확보(레지스트리 pull
    #      또는 로컬 빌드). 보존된 OCI 이미지 pull 이 정규 경로.
    #   2) 레포를 마운트해 컨테이너 진입(pixi 로 GDAL/GEOS/PROJ/uv 고정된 환경).
    #   3) lock_action 에 따라:
    #        GENERATE → `uv lock --script <script>` 후 커밋 대상으로 남김
    #        FROZEN   → `uv run --frozen --script <script>`
    #        RELOCK   → `uv lock --script <script>` (의존성 의도적 변경 = 새 버전 취급)
    #   4) `uv run --script <script>` 로 처리 실행.
    #   래퍼 세부 인자·구현은 pipeline-architecture.md '미해결' 참조.
    raise NotImplementedError(
        "컨테이너 실행은 아직 미구현입니다(설계상 '미해결'). "
        "위 계획은 확정되었고, docker/uv 연동만 채우면 됩니다."
    )
