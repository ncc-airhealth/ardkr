# /// script
# dependencies = [
#   "geopandas==1.1.2",
#   "pyarrow==25.0.0",
#   "pystac[validation]==1.15.1",
#   "ardkr[pipeline] @ git+https://github.com/ncc-airhealth/ardkr.git@main#subdirectory=ardkr",
# ]
#
# [tool.ardkr]
# image = "2026.07.21"
# ///

"""
한반도 군사분계선(MDL)과 비무장지대(DMZ) 경계 데이터셋.

## 주의사항

- 원본 item 설명은 EPSG:5181을 적지만 서비스 응답은 EPSG:5186이다. 서비스 응답을 따름
- 시간 범위의 시작은 정전협정 발효 시각, 끝은 원본 데이터 기준일로 해석함
- 원본이 속성 컬럼 의미를 설명하지 않음
- 두 레이어의 공간적 관계(군사분계선이 DMZ 중심선인지 등)를 원본이 명시하지 않음
- 한국에스리가 병합 외 가공을 했는지는 밝혀져 있지 않음
"""

from __future__ import annotations

import geopandas as gpd
import pystac
from ardkr.pipeline import CollectionBuilder

EPSG = 4326
SOURCE_URL = (
    "https://services.arcgis.com/rOo16HdIMeOBI4Mb/arcgis/rest/services/"
    "KR_MDL_DMZ/FeatureServer/{layer_id}/"
    "query?where=1%3D1&outFields=*&returnGeometry=true&f=geojson&outSR={epsg}"
)

# fmt: off
COLLECTION_STAC_CONTENT = {

    # schema
    "type": "Collection",
    "stac_version": "1.1.0",
    "stac_extensions": [
        "https://stac-extensions.github.io/proj/v2.0.0/schema.json",
    ],

    # version
    "version": "3.0.1",
    "experimental": True,

    # core: searchables
    "id": "esri-mdl-dmz",
    "keywords": ["군사분계선", "비무장지대", "MDL", "DMZ", "정전협정"],
    "extent": {
        "spatial": {"bbox": [[-180.0, -90.0, 180.0, 90.0]]},
        "temporal": {"interval": [["1953-07-27T13:00:00Z", "2025-05-01T00:00:00Z"]]},
    },
    "description": __doc__,

    # core: license & references
    "license": "proprietary",
    "providers": [
        {
            "name": "환경부",
            "roles": ["licensor"],
            "url": "https://www.me.go.kr/",
        },
        {
            "name": "한국환경연구원",
            "roles": ["producer"],
            "url": "https://data.neins.go.kr/",
        },
        {
            "name": "한국에스리",
            "roles": ["processor", "host"],
            "url": "https://www.esrikr.com/",
        },
    ],
    "links": [
        {
            "href": "https://portal.esrikr.com/arcgis/rest/services/Hosted/KR_MDL_DMZ/FeatureServer",
            "title": "FeatureServer",
            "rel": "via",
        },
        {
            "href": "https://www.arcgis.com/home/item.html?id=38abc1ea73d94ab18e55f7b0ee13c812",
            "title": "ArcGIS item",
            "rel": "via",
        },
        {
            "href": "https://data.neins.go.kr/detail/dts-eh03eVuTQu",
            "title": "군사분계선 원본",
            "rel": "via",
        },
        {
            "href": "https://data.neins.go.kr/detail/dts-FeJLArLgg1",
            "title": "비무장지대 원본",
            "rel": "via",
        },
        {
            "href": "https://www.archives.gov/milestone-documents/"
            "armistice-agreement-restoration-south-korean-state",
            "title": "정전협정",
            "rel": "related",
        },
        {
            "href": "https://repository.kei.re.kr/handle/2017.oak/22531",
            "title": "KEI DMZ 공간역 보고서",
            "rel": "related",
        },
        {
            "href": "https://www.arcgis.com/home/item.html?id=38abc1ea73d94ab18e55f7b0ee13c812",
            "title": "원본 item 이용 조건",
            "rel": "license",
        },
        {
            "href": "https://data.neins.go.kr/copyright",
            "title": "원본 배포처 저작권 정책",
            "rel": "license",
        },
    ]
}
# fmt: on


class PipelineCollection(CollectionBuilder):
    collection = pystac.Collection.from_dict(COLLECTION_STAC_CONTENT)
    checklist = {
        "데이터를 QGIS로 로드하여 베이스맵과의 위치 일관성을 확인": True,
        "providers 필드의 name·roles가 실제 제공 주체와 맞는지 검증": True,
        "기간의 끝을 원본 기준일로 두는 해석이 맞는가": False,
    }

    def process(self):
        mdl = self._add_mdl_asset()
        dmz = self._add_dmz_asset()
        self._update_collection_spatial_extent(mdl, dmz)

    def verify_auto(self):
        self._verify_mdl_file()
        self._verify_dmz_file()

    def _add_mdl_asset(self):
        asset = self.collection.pipe.define_asset(
            key="mdl",
            bucket="ardkr-data",
            filename="mdl.parquet",
            title="Military Demarcation Line (MDL)",
            roles=["data"],
            media_type="application/vnd.apache.parquet",
        )

        url = SOURCE_URL.format(layer_id=0, epsg=EPSG)
        gdf = gpd.read_file(url, driver="GeoJSON")
        gdf.to_parquet(asset.pipe.path, compression="zstd")
        asset.pipe.apply_digest()

        asset.ext.add("table")
        asset.ext.table.columns = [
            {"name": name, "type": str(dtype)}
            for name, dtype in gdf.dtypes.items()
        ]
        asset.ext.table.row_count = len(gdf)
        asset.ext.table.primary_geometry = gdf.geometry.name

        asset.ext.add("proj")
        asset.ext.proj.epsg = EPSG
        return gdf

    def _add_dmz_asset(self):
        asset = self.collection.pipe.define_asset(
            key="dmz",
            bucket="ardkr-data",
            filename="dmz.parquet",
            title="Demilitarized Zone (DMZ)",
            roles=["data"],
            media_type="application/vnd.apache.parquet",
        )
        url = SOURCE_URL.format(layer_id=1, epsg=EPSG)
        gdf = gpd.read_file(url, driver="GeoJSON")
        gdf.to_parquet(asset.pipe.path, compression="zstd")
        asset.pipe.apply_digest()

        asset.ext.add("table")
        asset.ext.table.columns = [
            {"name": name, "type": str(dtype)}
            for name, dtype in gdf.dtypes.items()
        ]
        asset.ext.table.row_count = len(gdf)
        asset.ext.table.primary_geometry = gdf.geometry.name

        asset.ext.add("proj")
        asset.ext.proj.epsg = EPSG
        return gdf
    
    def _update_collection_spatial_extent(
        self, mdl: gpd.GeoDataFrame, dmz: gpd.GeoDataFrame
    ):
        minx = min(mdl.total_bounds[0], dmz.total_bounds[0])
        miny = min(mdl.total_bounds[1], dmz.total_bounds[1])
        maxx = max(mdl.total_bounds[2], dmz.total_bounds[2])
        maxy = max(mdl.total_bounds[3], dmz.total_bounds[3])
        self.collection.extent.spatial.bboxes = [[minx, miny, maxx, maxy]]

    def _verify_mdl_file(self):
        gdf = gpd.read_parquet(self.collection.assets["mdl"].pipe.path)
        assert gdf.crs.to_epsg() == EPSG, f"좌표계가 원본과 다릅니다: {gdf.crs}"
        assert len(gdf) > 0, "데이터가 비었습니다."

    def _verify_dmz_file(self):
        gdf = gpd.read_parquet(self.collection.assets["dmz"].kr.path)
        assert gdf.crs.to_epsg() == EPSG, f"좌표계가 원본과 다릅니다: {gdf.crs}"
        assert len(gdf) > 0, "데이터가 비었습니다."


if __name__ == "__main__":
    PipelineCollection.build()
