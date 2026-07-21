"""geovars.catalog — STAC 카탈로그 로딩·검색.

extra: [catalog]  (pip install "geovars[catalog]")

stac-metadata/ 의 파일 기반 STAC 카탈로그를 pystac 으로 로드하고, 상대경로를
해석해 collection/item 을 검색한다. 카탈로그 갱신은 load-mutate-save 방식.
세부: knowledge/decisions/catalog-and-access.md
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    import pystac
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'geovars.catalog 는 pystac 이 필요합니다: pip install "geovars[catalog]"'
    ) from exc

# TODO: load_catalog() / search() 등 구현.


def register_collection_version(catalog_root: str | Path, collection: pystac.Collection, version: str) -> None:
    """collection을 `<catalog_root>/<collection.id>/version=<version>/`에 self-contained로
    저장하고, 루트 `catalog.json`의 child link를 이 버전으로 교체한다(과거 버전 파일은 지우지
    않고 보존 — 루트는 최신만 노출, 레포는 전-버전 보관.
    [/decisions/catalog-and-access.md](../../../knowledge/decisions/catalog-and-access.md)
    "카탈로그 구조 vs 레포"). 버전 디렉터리는 Hive 스타일 `version=<version>`으로 self-describing
    하게 짓는다(S3 asset key도 동일 컨벤션).

    pystac 기본 직렬화(`ensure_ascii=True`)는 한국어를 `\\uXXXX`로 이스케이프해 diff 리뷰를
    막으므로, 저장된 모든 JSON을 `ensure_ascii=False`로 재직렬화한다
    ([/decisions/catalog-and-access.md](../../../knowledge/decisions/catalog-and-access.md)
    "root catalog.json 구현").
    """
    catalog_root = Path(catalog_root)
    version_segment = f"version={version}"
    collection_dir = catalog_root / collection.id / version_segment
    # 끝에 "/"가 없으면 pystac이 버전 문자열(점 포함)을 파일명+확장자로 오인해 마지막 경로
    # 조각을 통째로 잘라버린다 — 반드시 트레일링 슬래시로 디렉터리임을 명시한다.
    collection.normalize_and_save(f"{collection_dir}/", catalog_type=pystac.CatalogType.SELF_CONTAINED)

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
    catalog_path.write_text(json.dumps(catalog_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for json_path in catalog_root.rglob("*.json"):
        if json_path == catalog_path:
            continue
        data = json.loads(json_path.read_text(encoding="utf-8"))
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
