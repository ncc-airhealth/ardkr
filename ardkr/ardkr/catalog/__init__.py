"""ardkr.catalog — STAC 카탈로그 로딩·검색.

extra: [catalog]  (pip install "ardkr[catalog]")

stac-metadata/ 의 파일 기반 STAC 카탈로그를 pystac 으로 로드하고, 상대경로를
해석해 collection/item 을 검색한다. 카탈로그 갱신은 load-mutate-save 방식.
세부: .agents/skills/pipeline-publish-verify/SKILL.md
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    import pystac
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'ardkr.catalog 는 pystac 이 필요합니다: pip install "ardkr[catalog]"'
    ) from exc

# TODO: load_catalog() / search() 등 구현.


def register_collection(
    collection: pystac.Collection, version: str, catalog_root: str | Path = "stac-metadata"
) -> None:
    """collection을 `<catalog_root>/<collection.id>/version=<version>/`에 self-contained로
    저장하고, 루트 `catalog.json`의 child link를 이 버전으로 교체한다. 과거 버전 파일은
    지우지 않고 보존한다 — 루트는 최신만 노출, 레포는 전-버전 보관. 버전 디렉터리는 Hive
    스타일 `version=<version>`으로 self-describing하게 짓는다(S3 asset key도 동일
    컨벤션). `pystac.layout.TemplateLayoutStrategy`는 쓰지 않는다 — 대상이 트리 root일 때
    템플릿을 무시하고 `BestPracticesLayoutStrategy`로 폴백해, 이 collection 서브트리만
    증분 등록하는 방식과 맞지 않는다.

    `catalog_root` 기본값은 cwd 기준 상대경로다 — `pipeline/run.py`가 Docker 컨테이너의 cwd를
    항상 레포 루트로 고정하므로(`-w /workspace`), 처리 스크립트는 이 인자를 생략해도 된다.
    `pipeline/run.py`를 거치지 않고 다른 위치에서 직접 실행하는 경우에만 명시적으로 넘긴다.
    내부에서 곧바로 절대경로로 변환한다 — 상대경로를 그대로 pystac의 `normalize_and_save`에
    넘기면 버전 세그먼트 없는 flat 경로에 collection.json/item이 중복 생성되는 버그가 있다.

    pystac 기본 직렬화(`ensure_ascii=True`)는 한국어를 `\\uXXXX`로 이스케이프해 diff 리뷰를
    막으므로, 저장된 모든 JSON을 `ensure_ascii=False`로 재직렬화한다.
    """
    catalog_root = Path(catalog_root).resolve()
    version_segment = f"version={version}"
    collection_dir = catalog_root / collection.id / version_segment
    # 끝에 "/"가 없으면 pystac이 버전 문자열(점 포함)을 파일명+확장자로 오인해 마지막 경로
    # 조각을 통째로 잘라버린다 — 반드시 트레일링 슬래시로 디렉터리임을 명시한다.
    collection.normalize_and_save(
        f"{collection_dir}/", catalog_type=pystac.CatalogType.SELF_CONTAINED
    )

    catalog_path = catalog_root / "catalog.json"
    catalog_json = json.loads(catalog_path.read_text(encoding="utf-8"))
    prefix = f"./{collection.id}/"
    catalog_json["links"] = [
        link
        for link in catalog_json["links"]
        if not (link.get("rel") == "child" and link.get("href", "").startswith(prefix))
    ]
    catalog_json["links"].append(
        {
            "rel": "child",
            "href": f"{prefix}{version_segment}/collection.json",
            "type": "application/json",
            "title": collection.title or collection.id,
        }
    )
    catalog_path.write_text(
        json.dumps(catalog_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for json_path in catalog_root.rglob("*.json"):
        if json_path == catalog_path:
            continue
        data = json.loads(json_path.read_text(encoding="utf-8"))
        json_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
