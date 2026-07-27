# /// script
# dependencies = [
#   "geopandas==1.1.2",
#   "pyarrow==25.0.0",
#   "pystac[validation]==1.15.1",
#   "python-dotenv==1.1.0",
#   "ardkr[storage] @ git+file:///workspace#subdirectory=ardkr",
# ]
#
# [tool.ardkr]
# image = "2026.07.21"
# ///

"""
한반도 군사분계선(MDL)과 비무장지대(DMZ) 경계 데이터셋이다.
한국에스리 ArcGIS Living Atlas hosted FeatureServer에서 받아 GeoParquet으로 저장했다.

## 처리

원본 서비스 좌표계는 EPSG:5186이다.
`outSR=4326`으로 요청해 서버가 변환한 결과를 EPSG:4326으로 저장한다.

## 주의사항

- 원본 item 설명은 EPSG:5181을 적지만 서비스 응답은 EPSG:5186이다. 서비스 응답을 따름
- 시간 범위의 시작은 정전협정 발효 시각, 끝은 원본 데이터 기준일로 해석함
- 원본이 속성 컬럼 의미를 설명하지 않음. 컬럼은 이름·타입만 `table:columns`에 남김
- 두 레이어의 관계(군사분계선이 DMZ 중심선인지 등)를 원본이 명시하지 않음
- 한국에스리가 병합 외 가공을 했는지는 밝혀져 있지 않음
- KEI 보고서가 정의한 DMZ 공간역과 이 데이터가 같은 산출물인지는 원본이 밝히지 않음
- 원본 데이터셋 상세 페이지는 자바스크립트로 그려져 공공누리 유형을 문서로 확인하지 못함
- 재배포 허용 여부가 미확인임
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import ardkr.storage as rs
import geopandas as gpd
import pystac as ps
from dotenv import load_dotenv
from pystac.extensions.table import Column

# 상수 ------------------------------------------------------------------------
load_dotenv()

# 사람이 실행마다 조정하는 값
VERSION = "3.0.1"
EXPERIMENTAL = True  # 라이선스 확인 전까지 True. 해제는 사람만 한다 (repo-rule).

# 고정 상수
CATALOG_ROOT = "stac-metadata"
SOURCE_SERVICE_URL = "https://portal.esrikr.com/arcgis/rest/services/Hosted/KR_MDL_DMZ/FeatureServer"
SOURCE_ITEM_URL = (
    "https://www.arcgis.com/home/item.html?id=38abc1ea73d94ab18e55f7b0ee13c812"
)
KEI_MDL_URL = "https://data.neins.go.kr/detail/dts-eh03eVuTQu"
KEI_DMZ_URL = "https://data.neins.go.kr/detail/dts-FeJLArLgg1"
ARMISTICE_URL = (
    "https://www.archives.gov/milestone-documents/"
    "armistice-agreement-restoration-south-korean-state"
)
KEI_REPORT_URL = "https://repository.kei.re.kr/handle/2017.oak/22531"
COPYRIGHT_POLICY_URL = "https://data.neins.go.kr/copyright"
ASSET_EPSG = 4326
ARMISTICE_EFFECTIVE_AT = datetime(1953, 7, 27, 13, 0, tzinfo=UTC)
SOURCE_REFERENCE_AT = datetime(2025, 5, 1, tzinfo=UTC)
PROCESSED_AT = datetime.now(UTC)

LAYERS: dict[str, dict[str, Any]] = {
    "mdl": {
        "layer_id": 0,
        "title": "군사분계선",
        "description": "정전협정이 정한 군사분계선. 원본 FeatureServer 레이어 0.",
    },
    "dmz": {
        "layer_id": 1,
        "title": "비무장지대",
        "description": "군사분계선에 접한 비무장지대. 원본 FeatureServer 레이어 1.",
    },
}


# collection ------------------------------------------------------------------
c = ps.Collection(
    id="arcgis-mdl-dmz",
    title="군사분계선/비무장지대",
    description=__doc__,
    keywords=["군사분계선", "비무장지대", "MDL", "DMZ", "정전협정"],
    extent=ps.Extent(
        spatial=ps.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
        temporal=ps.TemporalExtent(
            [[ARMISTICE_EFFECTIVE_AT, SOURCE_REFERENCE_AT]]
        ),
    ),
    license="other",
    providers=[
        ps.Provider(
            name="환경부",
            description="원본 item이 표기한 권리자. 한국에스리 포털 item은 같은 데이터의 권리자를 'Ministry of Climate, Energy and Environment'로 적는다.",
            roles=["licensor"],
            url="https://www.me.go.kr/",
        ),
        ps.Provider(
            name="한국환경연구원",
            description="국토환경성평가지도 자료제공서비스 운영기관. 원본 shapefile의 배포처다. 형상을 직접 만든 주체인지는 원본이 밝히지 않는다.",
            roles=["producer"],
            url="https://data.neins.go.kr/",
        ),
        ps.Provider(
            name="한국에스리",
            description="원본 shapefile 두 종을 한 레이어로 병합해 ArcGIS Living Atlas에 게시하고 FeatureServer로 호스팅한다.",
            roles=["processor", "host"],
            url="https://www.esrikr.com/",
        ),
    ],
)
c.ext.add("version")
c.ext.version.apply(version=VERSION, experimental=EXPERIMENTAL)
c.add_link(
    ps.Link(
        rel="via",
        target=SOURCE_SERVICE_URL,
        media_type=ps.MediaType.HTML,
        title="FeatureServer",
    )
)
c.add_link(
    ps.Link(
        rel="via",
        target=SOURCE_ITEM_URL,
        media_type=ps.MediaType.HTML,
        title="ArcGIS item",
    )
)
c.add_link(
    ps.Link(
        rel="via",
        target=KEI_MDL_URL,
        media_type=ps.MediaType.HTML,
        title="군사분계선 원본",
    )
)
c.add_link(
    ps.Link(
        rel="via",
        target=KEI_DMZ_URL,
        media_type=ps.MediaType.HTML,
        title="비무장지대 원본",
    )
)
c.add_link(
    ps.Link(
        rel="related",
        target=ARMISTICE_URL,
        media_type=ps.MediaType.HTML,
        title="정전협정",
    )
)
c.add_link(
    ps.Link(
        rel="describedby",
        target=KEI_REPORT_URL,
        media_type=ps.MediaType.HTML,
        title="KEI DMZ 공간역 보고서",
    )
)
c.add_link(
    ps.Link(
        rel="license",
        target=SOURCE_ITEM_URL,
        media_type=ps.MediaType.HTML,
        title="원본 item 이용 조건",
    )
)
c.add_link(
    ps.Link(
        rel="license",
        target=COPYRIGHT_POLICY_URL,
        media_type=ps.MediaType.HTML,
        title="원본 배포처 저작권 정책",
    )
)


# main ------------------------------------------------------------------------
def main():
    define_item_assets()
    build_item_from_source()
    register_collection()
    verify_registration()


# stage -----------------------------------------------------------------------
def define_item_assets():
    """collection의 item-asset 정의를 만든다.

    이 collection의 모든 item이 공유하는 asset 계약이다. 실행마다 값이 달라지는
    ``file``·``table`` 필드는 여기 두지 않고 실제 asset에 채운다.
    """
    definitions = {}
    for key, spec in LAYERS.items():
        definition = ps.ItemAssetDefinition(
            owner=c,
            properties={
                "title": spec["title"],
                "description": spec["description"],
                "roles": ["data"],
                "media_type": ps.MediaType.VND_APACHE_PARQUET,
            },
        )
        definition.ext.add("proj")
        definition.ext.proj.apply(epsg=ASSET_EPSG)
        definitions[key] = definition

    # setter가 대입 시점에 dict로 직렬화한다. 설정을 끝낸 뒤 한 번에 대입한다.
    c.item_assets = definitions


def build_item_from_source():
    """원본을 받아 GeoParquet으로 저장하고 item과 asset을 구성한다.

    parquet은 저장소의 로컬 미러(캐시)에 쓴다. 원격 업로드는 register 단계가 맡는다.
    """
    frames = {
        key: _read_layer(spec["layer_id"]) for key, spec in LAYERS.items()
    }
    bounds = _union_bounds(frames.values())

    item = ps.Item(
        id=c.id,
        geometry=_bbox_polygon(bounds),
        bbox=list(bounds),
        datetime=None,
        start_datetime=ARMISTICE_EFFECTIVE_AT,
        end_datetime=SOURCE_REFERENCE_AT,
        collection=c.id,
        properties={},
    )
    # 데이터의 시간 범위와 구분해, 이 스냅샷을 만든 시각을 따로 적는다.
    item.common_metadata.created = PROCESSED_AT
    c.add_item(item)

    for key, gdf in frames.items():
        path = _asset_path(item, key)
        gdf.to_parquet(path.cache_path, compression="zstd")
        item.assets[key] = _build_asset(key, gdf, path, owner=item)

    c.update_extent_from_items()


def register_collection():
    """STAC metadata를 저장한다.

    ``EXPERIMENTAL``이 False일 때만 asset이 원격 저장소로 올라간다.
    """
    rs.register_collection(collection=c, catalog_root=CATALOG_ROOT)


def verify_registration():
    """등록 결과를 검증하고, 사람이 판정할 항목을 보고한다.

    기계가 판정할 수 있는 것은 실패 시 예외로 멈춘다. 해석이 필요한 항목은
    보고만 하고 사람의 판정을 기다린다.
    """
    _verify_saved_stac()
    _verify_saved_assets()
    _report_for_human_review()


# util ------------------------------------------------------------------------
def _read_layer(layer_id: int) -> gpd.GeoDataFrame:
    """FeatureServer 레이어 하나를 GeoJSON으로 전량 받아온다."""
    url = (
        f"{SOURCE_SERVICE_URL}/{layer_id}/query"
        "?where=1%3D1"
        "&outFields=*"
        "&returnGeometry=true"
        "&f=geojson"
        f"&outSR={ASSET_EPSG}"
    )
    return gpd.read_file(url, driver="GeoJSON")


def _asset_path(item: ps.Item, key: str) -> rs.ObjectPath:
    """asset key에 대응하는 저장소 경로를 계산한다."""
    return rs.object_path(collection=c, item=item, filename=f"{key}.parquet")


def _union_bounds(frames) -> tuple[float, float, float, float]:
    """여러 GeoDataFrame을 감싸는 bbox를 계산한다."""
    boxes = [tuple(float(v) for v in frame.total_bounds) for frame in frames]
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def _bbox_polygon(bounds: tuple[float, float, float, float]) -> dict[str, Any]:
    """bbox를 GeoJSON Polygon으로 만든다."""
    minx, miny, maxx, maxy = bounds
    ring = [
        [minx, miny],
        [maxx, miny],
        [maxx, maxy],
        [minx, maxy],
        [minx, miny],
    ]
    return {"type": "Polygon", "coordinates": [ring]}


def _build_asset(
    key: str, gdf: gpd.GeoDataFrame, path: rs.ObjectPath, *, owner: ps.Item
) -> ps.Asset:
    """item-asset 정의로 asset을 만들고 파일·테이블 실측값을 채운다."""
    asset = c.item_assets[key].create_asset(href=path.s3_key)
    asset.set_owner(owner)
    asset.ext.add("file")
    asset.ext.file.apply(**path.file_ext_props)
    asset.ext.add("table")
    asset.ext.table.columns = [
        Column({"name": name, "type": str(dtype)})
        for name, dtype in gdf.dtypes.items()
    ]
    asset.ext.table.row_count = len(gdf)
    asset.ext.table.primary_geometry = gdf.geometry.name
    return asset


def _saved_item() -> ps.Item:
    """저장된 카탈로그에서 이 collection의 item을 다시 읽는다."""
    catalog = ps.Catalog.from_file(str(Path(CATALOG_ROOT) / "catalog.json"))
    saved = catalog.get_child(c.id)
    if saved is None:
        raise AssertionError(f"카탈로그에 collection이 없습니다: {c.id}")
    items = list(saved.get_items())
    if len(items) != 1:
        raise AssertionError(f"item이 1개여야 합니다. 실제: {len(items)}개")
    return items[0]


def _verify_saved_stac():
    """저장된 STAC을 다시 읽어 스키마와 구조를 검증한다.

    메모리 객체는 link href가 아직 비어 있어 스키마 검증을 통과하지 못한다.
    그래서 반드시 저장된 파일에서 다시 읽어 검증한다.
    """
    item = _saved_item()
    collection = item.get_collection()
    if collection is None:
        raise AssertionError("item이 collection을 가리키지 않습니다.")

    collection.validate()
    item.validate()

    if set(item.assets) != set(LAYERS):
        raise AssertionError(f"asset key가 다릅니다: {sorted(item.assets)}")
    if collection.ext.version.version != VERSION:
        raise AssertionError("저장된 version이 스크립트 상수와 다릅니다.")


def _verify_saved_assets():
    """저장된 asset 파일을 다시 읽어 STAC이 적은 값과 맞는지 검증한다."""
    item = _saved_item()
    for key, asset in item.assets.items():
        path = _asset_path(item, key)
        size, checksum = rs.file_digest(path.cache_path)
        if (checksum, size) != (asset.ext.file.checksum, asset.ext.file.size):
            raise AssertionError(f"{key}: checksum·size가 STAC과 다릅니다.")

        gdf = gpd.read_parquet(path.cache_path)
        if len(gdf) != asset.ext.table.row_count:
            raise AssertionError(f"{key}: 행 수가 table:row_count와 다릅니다.")
        if gdf.crs is None or gdf.crs.to_epsg() != ASSET_EPSG:
            raise AssertionError(f"{key}: 좌표계가 원본과 다릅니다: {gdf.crs}")
        if gdf.empty:
            raise AssertionError(f"{key}: 데이터가 비었습니다.")
        if gdf.geometry.isna().any() or gdf.geometry.is_empty.any():
            raise AssertionError(f"{key}: 빈 geometry가 있습니다.")
        if not _within(gdf.total_bounds, item.bbox):
            raise AssertionError(f"{key}: 범위가 item bbox를 벗어납니다.")


def _within(bounds, bbox) -> bool:
    """bounds가 bbox 안에 들어오는지 본다."""
    return (
        bounds[0] >= bbox[0]
        and bounds[1] >= bbox[1]
        and bounds[2] <= bbox[2]
        and bounds[3] <= bbox[3]
    )


def _report_for_human_review():
    """사람이 판정할 항목을 출력한다.

    실행기가 컨테이너에 stdin을 붙이지 않으므로 입력을 기다리지 않는다.
    사람이 이 출력을 읽고 판정한다.
    """
    item = _saved_item()
    print("\n=== 등록 결과 ===")
    print(f"collection : {c.id} v{VERSION} experimental={EXPERIMENTAL}")
    print(f"license    : {c.license}")
    print(f"기간       : {ARMISTICE_EFFECTIVE_AT} ~ {SOURCE_REFERENCE_AT}")
    print(f"처리 시각  : {PROCESSED_AT}")
    print(f"bbox       : {item.bbox}")

    for key, asset in item.assets.items():
        gdf = gpd.read_parquet(_asset_path(item, key).cache_path)
        invalid = int((~gdf.geometry.is_valid).sum())
        print(f"\n[{key}] {asset.title} — {asset.href}")
        print(f"  행 수    : {len(gdf)}")
        print(f"  geometry : {sorted(gdf.geom_type.unique())}")
        print(f"  invalid  : {invalid}개")
        print(f"  컬럼     : {[(n, str(t)) for n, t in gdf.dtypes.items()]}")
        print(f"  크기     : {asset.ext.file.size} bytes")

    print("\n--- 사람이 판정할 항목 ---")
    print("1. 재배포 허용을 확인받았는가 (원본 표기는 all rights reserved)")
    print("2. 원본 데이터셋에 공공누리 표시가 있는가. 유형은 무엇인가")
    print("3. providers의 name·roles가 실제 제공 주체와 맞는가")
    print("4. via·license 링크만으로 출처·이용 조건이 충분히 드러나는가")
    print("5. 기간의 끝을 원본 기준일로 두는 해석이 맞는가")
    print("6. invalid geometry가 있다면 원본 문제인가, 허용할 것인가")
    print("7. 위가 다 풀렸을 때 EXPERIMENTAL을 내릴 것인가 (사람만 결정)")


# 실행 ------------------------------------------------------------------------
if __name__ == "__main__":
    main()
