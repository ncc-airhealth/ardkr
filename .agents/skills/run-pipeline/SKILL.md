---
name: run-pipeline
description: Use when actually executing a pipeline/process/<collection-id>.py script (python pipeline/run.py) or figuring out lock/--relock behavior.
---

# run-pipeline

처리 스크립트를 실제로 실행하는 방법.

```bash
python pipeline/run.py <collection-id> [--relock]
```

- 스크립트 상단 `[tool.geovars] image`가 가리키는 Docker+pixi 컨테이너 안에서 `uv run --script`로 실행된다. lock이 없으면 생성하고, 있으면 그대로 쓴다(frozen). `--relock`은 의존성을 의도적으로 바꿀 때만 쓴다. 전체 동작은 `pipeline/run.py`의 모듈 docstring이 SSOT다.
- lock이 새로 생성/갱신됐으면 커밋한다.
- 재실행 결과는 `git diff --stat stac-metadata/`로 확인한다 — 입력이 그대로면 diff가 없어야 한다.
- 스크립트를 고치면 `uvx ruff format <path>`와 `uvx ruff check --fix <path>`를 돌린다. 설정은 레포 루트 `ruff.toml`.
- `PUBLISH_MODE = "local"`로 반복 개발하는 동안은 `verify_uploaded()`가 항상 실패한다 — R2에 아무것도 없으니 정상이다([pipeline-publish-verify](../pipeline-publish-verify/SKILL.md)).
