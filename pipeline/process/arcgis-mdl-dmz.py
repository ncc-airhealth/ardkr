# /// script
# dependencies = [
#   "duckdb==1.5.5",
#   "geopandas==1.1.2",
#   "pyarrow==25.0.0",
#   "pystac==1.15.1",
#   "python-dotenv==1.1.0",
#   "ardkr[storage] @ git+file:///workspace#subdirectory=ardkr",
# ]
#
# [tool.ardkr]
# image = "2026.07.21"
# ///

"""
# 소개
ArcGIS API에서 제공하는 군사분계선(MDL) 및 비무장지대(DMZ) 데이터.

인프라 검증용 겸 실사용 collection이다.
인프라 검증 대상은 아래와 같다.
- 파이프라인 코드 동작
- S3 호환 스토리지로의 Asset 업로드
- STAC metadata 등록
"""

from __future__ import annotations

from datetime import datetime
from pprint import pprint

import ardkr.storage as rs
import geopandas as gpd
import pystac as ps
from dotenv import load_dotenv

load_dotenv()

# developer configurable
VERSION = "3.0.1"
EXPERIMENTAL = True

# collection constants
ARMISTICE_STARTED_AT = datetime.fromisoformat("1953-07-27T22:00:00+09:00")
PROCESSED_AT = datetime.now()
SOURCE_EPSG = 4326


# define collection ----------------------------------------------------------
c = ps.Collection(
    id="arcgis-mdl-dmz",
    title="ArcGIS 군사분계선/비무장지대",
    keywords=["ArcGIS", "MDL", "DMZ", "Military Demarcation Line"],
    description=__doc__,
    extent=ps.Extent(
        spatial=ps.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
        temporal=ps.TemporalExtent([[ARMISTICE_STARTED_AT, PROCESSED_AT]]),
    ),
    license="proprietary",
    providers=[
        ps.Provider(name="ArcGIS", roles=["host", "producer", "licensor"])
    ],
)
c.ext.add("version")
c.ext.version.apply(version=VERSION, experimental=EXPERIMENTAL)


# process --------------------------------------------------------------------
def main():
    """main function"""
    define_item_asset()
    define_item()
    register_collection()
    test()


def define_item_asset():
    """define item-asset definition for mdl and dmz"""
    # mdl
    mdl = ps.ItemAssetDefinition(
        owner=c,
        properties={
            "title": "군사분계선",
            "description": "군사분계선 데이터",
            "roles": ["data"],
            "media_type": "application/parquet",
        },
    )
    mdl.ext.add("proj")
    mdl.ext.add("file")
    mdl.ext.add("table")
    mdl.ext.proj.apply(epsg=SOURCE_EPSG)

    # dmz
    dmz = ps.ItemAssetDefinition(
        owner=c,
        properties={
            "title": "비무장지대",
            "description": "비무장지대 데이터",
            "roles": ["data"],
            "media_type": "application/parquet",
        },
    )
    dmz.ext.add("proj")
    dmz.ext.add("file")
    dmz.ext.add("table")
    dmz.ext.proj.apply(epsg=SOURCE_EPSG)

    # register
    c.item_assets = {"mdl": mdl, "dmz": dmz}
    mdl.set_owner(c)
    dmz.set_owner(c)


def define_item():
    """define item"""

    # item
    item = ps.Item(
        id=c.id,
        geometry=None,
        bbox=None,
        datetime=None,
        start_datetime=ARMISTICE_STARTED_AT,
        end_datetime=PROCESSED_AT,
        collection=c.id,
        properties={},
    )
    c.add_item(item)

    # asset = mdl
    mdl_path = rs.object_path(collection=c, item=item, filename="mdl.parquet")
    mdl_gdf = _read_mdl()
    mdl_gdf.to_parquet(mdl_path.cache_path, compression="zstd")
    mdl_asset = c.item_assets["mdl"].create_asset(href=mdl_path.s3_key)
    mdl_asset.set_owner(item)
    mdl_asset.ext.add("file")
    mdl_asset.ext.file.apply(**mdl_path.file_ext_props)
    item.assets["mdl"] = mdl_asset

    # asset = dmz
    dmz_path = rs.object_path(collection=c, item=item, filename="dmz.parquet")
    dmz_gdf = _read_dmz()
    dmz_gdf.to_parquet(dmz_path.cache_path, compression="zstd")
    dmz_asset = c.item_assets["dmz"].create_asset(href=dmz_path.s3_key)
    dmz_asset.set_owner(item)
    dmz_asset.ext.add("file")
    dmz_asset.ext.file.apply(**dmz_path.file_ext_props)
    item.assets["dmz"] = dmz_asset

    # set extent for item & collection
    item.bbox = dmz_gdf.geometry.total_bounds
    c.update_extent_from_items()


def register_collection():
    """register collection"""
    rs.register_collection(collection=c)

def test():
    """test function"""
    _evaluate_stac_metadata()
    _evaluate_stac_assets_readable()

def _read_mdl() -> gpd.GeoDataFrame:
    """read mdl from ArcGIS API"""
    url = (
        "https://portal.esrikr.com/arcgis/rest/services/Hosted/"
        "KR_MDL_DMZ/FeatureServer/0/"
        "query?"
        "where=1%3D1"
        "&outFields=*"
        "&returnGeometry=true"
        "&f=geojson"
        f"&outSR={SOURCE_EPSG}"
    )
    gdf = gpd.read_file(url, driver="GeoJSON")
    return gdf


def _read_dmz() -> gpd.GeoDataFrame:
    """read dmz from ArcGIS API"""
    url = (
        "https://portal.esrikr.com/arcgis/rest/services/Hosted/"
        "KR_MDL_DMZ/FeatureServer/1/"
        "query?"
        "where=1%3D1"
        "&outFields=*"
        "&returnGeometry=true"
        "&f=geojson"
        f"&outSR={SOURCE_EPSG}"
    )
    gdf = gpd.read_file(url, driver="GeoJSON")
    return gdf

def _evaluate_stac_metadata():
    """evaluate stac metadata"""
    cat = ps.Catalog.from_file("stac-metadata/catalog.json")
    col = cat.get_child(c.id)

def _evaluate_stac_assets_readable():
    """evaluate stac assets readable"""
    for item in c.get_items():
        for key, asset in item.assets.items():
            asset.href
            duckdb.

            gdf = gpd.read_parquet()
            asset.read()
            pprint(asset.to_dict())
            raise Exception()
    print(c.item.assets["mdl"].to_dict())
    print(c.item.assets["dmz"].to_dict())

# run ------------------------------------------------------------------------
if __name__ == "__main__":
    main()
