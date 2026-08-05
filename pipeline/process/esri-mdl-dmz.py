# /// script
# dependencies = [
#   "geopandas==1.1.2",
#   "pyarrow==25.0.0",
#   "pystac[validation]==1.15.2",
#   "ardkr[pipeline] @ git+https://github.com/ncc-airhealth/ardkr.git@main#subdirectory=ardkr",
# ]
#
# [tool.ardkr]
# image = "2026.07.21"
# ///

"""
한반도 군사분계선(MDL)과 비무장지대(DMZ) 경계 데이터.

## 주의사항
- 연구·분석 참고용이다. 군사·행정 경계의 공식 확정본으로 보지 않는다.
- 한국에스리 쪽 문서에 적힌 가공은 shapefile 병합까지다. 그 밖의 가공 여부는 확인되지 않았다.
- live FeatureServer를 조회하므로, 나중에 서비스가 바뀌면 결과가 달라질 수 있다.
- 위치 정확도, 축척, 법적 효력은 원본에서 확인되지 않았다.

## 시점 관련 의사결정
- 정전협정 서명 시각이 아니라 발효 시각을 시작 시각으로 설정했다.
- 종료 시점은 비워 둔다. MDL·DMZ는 아직 유효하다.
- Esri ArcGIS item의 `Data Reference Date: 2025.05`를 데이터 기준월로 설정했다.
- NEINS 원본에는 2024년 생성·갱신 기록이 있고, FeatureServer layer의 lastEditDate는 2025-08-26이다.
- Collection `created`는 이 컬렉션 스냅샷을 파이프라인으로 만든 시각이다.

## 좌표계 관련 의사결정
- FeatureServer를 `outSR=4326`으로 조회했다.
- 서비스와 NEINS 원본 메타데이터는 `EPSG:5186`이다.
- ArcGIS item 문구만 `EPSG:5181`을 적는다. 원본 미터 좌표를 5181로 읽으면 위치가 크게 틀어지므로, 원본 좌표계는 서비스·NEINS를 따른다.
"""

from datetime import datetime, timezone

import geopandas as gpd
import pystac
from ardkr.pipeline import CollectionBuilder
from pystac.utils import datetime_to_str

EPSG = 4326
SOURCE_URL = (
    "https://portal.esrikr.com/arcgis/rest/services/Hosted/"
    "KR_MDL_DMZ/FeatureServer/{layer_id}/"
    "query?where=1%3D1&outFields=*&returnGeometry=true&f=geojson&outSR={epsg}"
)

# 실행 시 geometry bounds로 덮어쓴다. 초기값은 3.0.1에서 확인한 DMZ bbox.
KNOWN_BBOX = [
    126.64685893945881,
    37.83399740919223,
    128.3683860401958,
    38.635703428605204,
]

COLUMN_DESCRIPTIONS = {
    "fid": "FeatureServer object ID (layer OID).",
    "objectid": "원본 shapefile object ID로 보이는 식별자.",
    "SHAPE__Length": (
        "ArcGIS virtual geometry length. 서비스 투영좌표계 기준 평면 길이(m). "
        "측지 거리가 아니다."
    ),
    "SHAPE__Area": (
        "ArcGIS virtual geometry area. 서비스 투영좌표계 기준 평면 면적(m²). "
        "측지 면적이 아니다."
    ),
    "geometry": (
        "주 geometry. 배포 CRS는 EPSG:4326. "
        "전국 단위 단일 feature이며 Z/M 없음."
    ),
}

# fmt: off
COLLECTION_STAC_CONTENT = {

    # schema
    "type": "Collection",
    "stac_version": "1.1.0",
    "stac_extensions": [],

    # version
    "version": "3.0.2",
    "experimental": False,

    # core: searchables
    "id": "esri-mdl-dmz",
    "title": "한반도 군사분계선·비무장지대 경계",
    "keywords": ["군사분계선", "비무장지대", "MDL", "DMZ", "정전협정", "휴전선"],
    "extent": {
        "spatial": {"bbox": [KNOWN_BBOX]},
        "temporal": {"interval": [["1953-07-27T13:00:00Z", None]]},
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
            "title": "FeatureServer (수집 원천)",
            "rel": "via",
            "type": "application/json",
        },
        {
            "href": "https://www.arcgis.com/home/item.html?id=38abc1ea73d94ab18e55f7b0ee13c812",
            "title": "ArcGIS item (공개 메타데이터)",
            "rel": "via",
            "type": "text/html",
        },
        {
            "href": "https://data.neins.go.kr/detail/dts-eh03eVuTQu",
            "title": "NEINS 군사분계선 원본",
            "rel": "via",
            "type": "text/html",
        },
        {
            "href": "https://data.neins.go.kr/detail/dts-FeJLArLgg1",
            "title": "NEINS 비무장지대 원본",
            "rel": "via",
            "type": "text/html",
        },
        {
            "href": "https://www.archives.gov/milestone-documents/"
            "armistice-agreement-restoration-south-korean-state",
            "title": "정전협정 원문·설명 (NARA)",
            "rel": "related",
            "type": "text/html",
        },
        {
            "href": "https://repository.kei.re.kr/handle/2017.oak/22531",
            "title": "KEI 2019 DMZ 공간역 정의 참고 보고서",
            "rel": "related",
            "type": "text/html",
        },
        {
            "href": "https://www.arcgis.com/home/item.html?id=38abc1ea73d94ab18e55f7b0ee13c812",
            "title": "환경부 all rights reserved (ArcGIS item)",
            "rel": "license",
            "type": "text/html",
        },
        {
            "href": "https://data.neins.go.kr/copyright",
            "title": "NEINS: 공공누리 없으면 담당 부서 사전협의",
            "rel": "license",
            "type": "text/html",
        },
    ]
}
# fmt: on


class PipelineCollection(CollectionBuilder):
    collection = pystac.Collection.from_dict(COLLECTION_STAC_CONTENT)
    checklist = {
        "QGIS에서 mdl·dmz 위치를 베이스맵과 대조했다": True,
        "providers 역할(환경부 licensor, KEI producer/원본제공, 한국에스리 processor·host)이 근거와 맞다": True,
        "temporal 시작=정전협정 발효, 끝=null, 데이터 기준월=2025-05 분리가 적절하다": True,
        "CRS 계보(item 문구 5181 / 서비스·NEINS 5186 / 배포 4326) 설명이 적절하다": True,
        "라이선스 요약(proprietary, 환경부 all rights reserved, NEINS는 공공누리 없으면 사전협의)이 적절하다": True,
        "thumbnail 미리보기가 데이터 내용을 대표한다": True,
    }

    def process(self):
        created = datetime.now(timezone.utc).replace(microsecond=0)
        self.collection.extra_fields["created"] = datetime_to_str(created)

        mdl = self._add_vector_asset(
            key="mdl",
            layer_id=0,
            filename="mdl.parquet",
            title="군사분계선 (MDL)",
            description=(
                "한반도를 남북으로 가르는 군사분계선. 흔히 휴전선이라고 부른다. "
                "FeatureServer layer 0 (KR_MDL). 전국 단위 LineString feature 한 행."
            ),
        )
        dmz = self._add_vector_asset(
            key="dmz",
            layer_id=1,
            filename="dmz.parquet",
            title="비무장지대 (DMZ)",
            description=(
                "정전협정에 따라 군사분계선에서 쌍방이 각 2 km씩 물러나 만든 비무장지대 경계. "
                "FeatureServer layer 1 (KR_DMZ). 전국 단위 Polygon feature 한 행."
            ),
        )
        self._add_thumbnail_asset()
        self._update_collection_spatial_extent(mdl, dmz)

    def verify_auto(self):
        assert self.collection.extra_fields.get("created"), (
            "collection created 시각이 없습니다."
        )
        self._verify_vector_asset(
            key="mdl",
            expected_columns=["fid", "SHAPE__Length", "objectid", "geometry"],
            expected_geom_types={"LineString"},
        )
        self._verify_vector_asset(
            key="dmz",
            expected_columns=[
                "fid",
                "SHAPE__Length",
                "objectid",
                "SHAPE__Area",
                "geometry",
            ],
            expected_geom_types={"Polygon"},
        )
        self._verify_thumbnail_asset()

    def _add_vector_asset(
        self,
        *,
        key: str,
        layer_id: int,
        filename: str,
        title: str,
        description: str,
    ) -> gpd.GeoDataFrame:
        """FeatureServer layer를 읽어 GeoParquet asset으로 등록한다."""
        asset = self.collection.pipe.define_asset(
            key=key,
            store="private",
            filename=filename,
            title=title,
            description=description,
            roles=["data"],
            media_type="application/vnd.apache.parquet",
        )

        url = SOURCE_URL.format(layer_id=layer_id, epsg=EPSG)
        gdf = gpd.read_file(url)
        if gdf.empty:
            raise ValueError(f"`{key}` 원본 조회 결과가 비었습니다: {url}")
        if gdf.crs is None:
            raise ValueError(f"`{key}` CRS가 없습니다: {url}")
        if gdf.crs.to_epsg() != EPSG:
            gdf = gdf.to_crs(epsg=EPSG)

        gdf.to_parquet(asset.pipe.path(), compression="zstd")
        asset.pipe.apply_digest()

        asset.ext.add("table")
        asset.ext.table.columns = [
            {
                "name": name,
                "type": str(dtype),
                **(
                    {"description": COLUMN_DESCRIPTIONS[name]}
                    if name in COLUMN_DESCRIPTIONS
                    else {}
                ),
            }
            for name, dtype in gdf.dtypes.items()
        ]
        asset.ext.table.row_count = len(gdf)
        asset.ext.table.primary_geometry = gdf.geometry.name

        asset.ext.add("proj")
        asset.ext.proj.epsg = EPSG
        return gdf

    def _add_thumbnail_asset(self):
        asset = self.collection.pipe.define_asset(
            key="thumbnail",
            store="open",
            filename="thumbnail.jpeg",
            title="미리보기",
            description="MDL·DMZ 경계 미리보기. 미리 둔 파일을 등록하고 digest만 계산한다.",
            roles=["thumbnail"],
            media_type="image/jpeg",
        )
        asset.pipe.apply_digest()

    def _update_collection_spatial_extent(
        self, mdl: gpd.GeoDataFrame, dmz: gpd.GeoDataFrame
    ):
        minx = min(mdl.total_bounds[0], dmz.total_bounds[0])
        miny = min(mdl.total_bounds[1], dmz.total_bounds[1])
        maxx = max(mdl.total_bounds[2], dmz.total_bounds[2])
        maxy = max(mdl.total_bounds[3], dmz.total_bounds[3])
        self.collection.extent.spatial.bboxes = [[minx, miny, maxx, maxy]]

    def _verify_vector_asset(
        self,
        *,
        key: str,
        expected_columns: list[str],
        expected_geom_types: set[str],
    ):
        gdf = gpd.read_parquet(self.collection.assets[key].pipe.path())
        actual_epsg = gdf.crs.to_epsg() if gdf.crs is not None else None
        assert actual_epsg == EPSG, f"`{key}` 좌표계가 원본과 다릅니다: {gdf.crs}"
        assert len(gdf) == 1, f"`{key}` 행 수가 1이 아닙니다: {len(gdf)}"
        assert list(gdf.columns) == expected_columns, (
            f"`{key}` 컬럼이 예상과 다릅니다: {list(gdf.columns)}"
        )

        geom = gdf.geometry.iloc[0]
        assert geom is not None and not geom.is_empty, f"`{key}` geometry가 비었습니다."
        assert geom.is_valid, f"`{key}` geometry가 유효하지 않습니다: {geom}"
        assert geom.geom_type in expected_geom_types, (
            f"`{key}` geometry 유형이 예상과 다릅니다: {geom.geom_type}"
        )

    def _verify_thumbnail_asset(self):
        path = self.collection.assets["thumbnail"].pipe.path()
        assert path.is_file(), f"thumbnail 파일이 없습니다: {path}"
        assert path.stat().st_size > 0, f"thumbnail 파일이 비었습니다: {path}"


if __name__ == "__main__":
    PipelineCollection.build()
