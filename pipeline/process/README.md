# pipeline/process

collection별 처리 스크립트를 **flat**하게 둔다. 파일명은 **collection id**와 동일:
`<collection-id>.py` (+ `<collection-id>.py.lock`).

각 스크립트는 자기완결(PEP 723 인라인 의존성 + 스크립트별 lock)이며, 상단
`[tool.geovars] image = "YYYY.MM.DD"`로 시스템 환경을 pin한다. 실행은 pipeline/ 워크스페이스의
실행기 [`../run.py`](../run.py)가 담당한다(image 해석 → 컨테이너 → lock → `uv run --script`).

세부: [`../../knowledge/decisions/pipeline-architecture.md`](../../knowledge/decisions/pipeline-architecture.md)
