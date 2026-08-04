# /// script
# dependencies = [
#   "ardkr[pipeline] @ git+https://github.com/ncc-airhealth/ardkr.git@main#subdirectory=ardkr",
#   "geopandas==1.1.2",
#   "pystac[validation]==1.15.2",
#   "tqdm==4.70.0",
# ]
#
# [tool.ardkr]
# image = "2026.07.21"
# ///

"""
SGIS 대한민국 행정구역 경계 데이터셋.
"""

import re

import geopandas as gpd
from ardkr.pipeline import CollectionBuilder
from pystac import Asset, Collection, Item
from shapely.geometry import box
from tqdm import tqdm

SOUTH_KOREA_BBOX = [124.0, 33.0, 132.0, 39.0]
SOUTH_KOREA_BBOX_GEOM = box(*SOUTH_KOREA_BBOX)


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
    "id": "sgis-adm-bnd",
    "keywords": ["SGIS", "통계청", "행정구역", "경계"],
    "extent": {
        "spatial": {"bbox": [SOUTH_KOREA_BBOX]},
        "temporal": {"interval": [["2000-01-01T00:00:00Z", "2026-07-01T00:00:00Z"]]},
    },
    "description": __doc__,

    # core: item asset definition
    "item_assets": {
        "sido": {
            "title": "sido level boundary",
            "type": "application/zip",
            "roles": ["data"]
        },
        "sigungu": {
            "title": "sigungu level boundary",
            "type": "application/zip",
            "roles": ["data"]
        },
        "dong": {
            "title": "dong level boundary",
            "type": "application/zip",
            "roles": ["data"]
        },
    },


    # core: license & references
    "license": "proprietary",
    "providers": [
        {
            "name": "통계지리정보서비스(SGIS)",
            "roles": ["producer"],
            "url": "https://sgis.mods.go.kr/",
        },
        {
            "name": "통계청",
            "roles": ["licensor"],
            "url": "https://mods.go.kr/",
        },
    ],
    "links": [
        {
            "href": "https://sgis.mods.go.kr/jsp/member/copyright.jsp",
            "title": "SGIS 저작권 정책",
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
    collection = Collection.from_dict(COLLECTION_STAC_CONTENT)
    checklist = {
        "데이터를 QGIS로 로드하여 베이스맵과의 위치 일관성을 확인": True,
        "데이터의 유효 시점 해석 방식에 대한 검토": False,
    }
    item_id_fmt = "sgis-adm-bnd-{year}-{quarter}q"
    default_epsg = 5179  # https://sgis.mods.go.kr/view/pss/dataProvdIntrcn

    def process(self):
        self._add_items()
        self._add_thumbnail_asset()
        self._update_collection_extent()

    def verify_auto(self):
        self._verify_item_has_3_assets()
        self._verify_bnd_asset_range()

    def _add_items(self):
        """FILES_INFO 기준으로 item 생성."""
        for item_group in tqdm(self.files_info, desc="adding items"):
            self._bnd_group_to_item(item_group)

    def _bnd_group_to_item(self, item_group: dict):
        """연·분기 그룹을 STAC item과 sido/sigungu/dong asset으로 등록."""
        year = item_group["year"]
        quarter = item_group["quarter"]
        item = Item(
            id=self.item_id_fmt.format(
                year=year, quarter=quarter
            ).replace("None", "0"),
            geometry=None,
            bbox=list(SOUTH_KOREA_BBOX),
            datetime=self._year_quarter_to_datetime(year, quarter),
            properties={},
        )
        item.ext.add("file")
        self.collection.add_item(item)

        for level in ["sido", "sigungu", "dong"]:
            asset = item.pipe.define_asset(
                key=level,
                store="private",
                filename=item_group[level],
                title=f"{level} boundary",
                roles=["data"],
                media_type="application/zip",
            )
            self._update_bnd_asset_metadata(asset)

    def _update_bnd_asset_metadata(self, asset: Asset):
        """shapefile zip을 읽어 table·proj·encoding 메타를 asset에 적는다."""
        vsi = f"/vsizip/{asset.pipe.path().resolve()}"
        encoding, table = self._read_with_encoding(vsi)

        asset.pipe.apply_digest()
        asset.ext.add("table")
        asset.ext.table.columns = [
            {"name": name, "type": str(dtype)}
            for name, dtype in table.dtypes.items()
        ] + [{"name": "geometry", "type": "geometry"}]
        asset.ext.table.row_count = len(table)
        asset.ext.table.primary_geometry = "geometry"
        asset.ext.table.storage_options = {"encoding": encoding}
        asset.ext.add("proj")
        asset.ext.proj.epsg = self.default_epsg

    def _read_with_encoding(self, vsi: str):
        """geometry를 읽지 않고 encoding과 table 메타데이터를 함께 구한다."""
        best_encoding, best_n, best_table = None, -1, None
        for encoding in ("utf-8", "cp949", "euc-kr"):
            try:
                table = gpd.read_file(
                    vsi,
                    encoding=encoding,
                    ignore_geometry=True,
                )
            except UnicodeDecodeError:
                continue

            nm_columns = [
                name for name in table.columns if name.lower().endswith("nm")
            ]
            if not nm_columns:
                raise ValueError(f"nm 컬럼 없음: {vsi}")

            n_ok, n_all = 0, 0
            for column in nm_columns:
                for value in table[column]:
                    text = str(value).strip()
                    n_all += 1
                    if (
                        text
                        and text.lower() not in ("none", "nan")
                        and re.fullmatch(r"[가-힣\d\s·・,.\-_]+", text)
                        and re.search(r"[가-힣]", text)
                    ):
                        n_ok += 1

            if n_all > 0 and n_ok == n_all:
                return encoding, table
            if n_ok > best_n:
                best_encoding, best_n, best_table = encoding, n_ok, table

        if best_encoding is not None and best_n > 0:
            return best_encoding, best_table
        raise ValueError(f"인코딩을 판별하지 못함: {vsi}")

    def _year_quarter_to_datetime(self, year, quarter):
        """연·분기를 유효 시점 날짜 문자열(YYYY-MM-DD)로 바꾼다."""
        if quarter == 2:
            mm, dd = 6, 30
        elif quarter == 4 or quarter is None:
            mm, dd = 12, 31
        else:
            raise NotImplementedError
        return f"{year}-{mm:02d}-{dd:02d}"

    def _add_thumbnail_asset(self):
        """collection thumbnail asset을 등록."""
        asset = self.collection.pipe.define_asset(
            key="thumbnail",
            store="open",
            filename="thumbnail.webp",
            title="Thumbnail",
            roles=["thumbnail"],
            media_type="image/webp",
        )
        asset.pipe.apply_digest()

    def _update_collection_extent(self):
        """item datetime 범위로 collection temporal extent를 갱신."""
        datetimes = [
            item.datetime
            for item in self.collection.get_all_items()
            if item.datetime is not None
        ]
        if not datetimes:
            return

        def as_str(v):
            return v if isinstance(v, str) else v.strftime("%Y-%m-%dT%H:%M:%SZ")

        ordered = sorted(datetimes, key=str)
        self.collection.extent.temporal.intervals = [
            [as_str(ordered[0]), as_str(ordered[-1])]
        ]

    def _verify_item_has_3_assets(self):
        """각 item의 asset이 3개인지 확인한다."""
        for item in self.collection.get_all_items():
            if len(item.assets) != 3:
                raise AssertionError(f"{item.id}: asset 개수 {len(item.assets)} != 3")

    def _verify_bnd_asset_range(self):
        """각 boundary asset이 전부 대한민국 범위에 포함되는지 확인"""
        items = self.collection.get_all_items()
        for item in tqdm(items, desc="verify boundary asset_range"):
            for key, asset in item.assets.items():
                encoding = asset.ext.table.storage_options["encoding"]
                asset_extent = (
                    gpd.read_file(asset.pipe.path(), encoding=encoding)
                    .set_crs(epsg=self.default_epsg)
                    .to_crs(epsg=4326)
                    .total_bounds
                )
                if not SOUTH_KOREA_BBOX_GEOM.covers(box(*asset_extent)):
                    raise AssertionError(
                        f"{item.id}/{key}: asset extent {asset_extent} "
                        f"is outside SOUTH_KOREA_BBOX {SOUTH_KOREA_BBOX}"
                    )

    @property
    def files_info(self) -> list[dict]:
        return [
            {
                "year": 1975,
                "quarter": 4,
                "sido": "bnd_sido_00_1975_4Q.zip",
                "sigungu": "bnd_sigungu_00_1975_4Q.zip",
                "dong": "bnd_dong_00_1975_4Q.zip",
            },
            {
                "year": 1980,
                "quarter": 4,
                "sido": "bnd_sido_00_1980_4Q.zip",
                "sigungu": "bnd_sigungu_00_1980_4Q.zip",
                "dong": "bnd_dong_00_1980_4Q.zip",
            },
            {
                "year": 1985,
                "quarter": 4,
                "sido": "bnd_sido_00_1985_4Q.zip",
                "sigungu": "bnd_sigungu_00_1985_4Q.zip",
                "dong": "bnd_dong_00_1985_4Q.zip",
            },
            {
                "year": 1990,
                "quarter": 4,
                "sido": "bnd_sido_00_1990_4Q.zip",
                "sigungu": "bnd_sigungu_00_1990_4Q.zip",
                "dong": "bnd_dong_00_1990_4Q.zip",
            },
            {
                "year": 1995,
                "quarter": None,
                "sido": "bnd_sido_00_1995.zip",
                "sigungu": "bnd_sigungu_00_1995.zip",
                "dong": "bnd_dong_00_1995.zip",
            },
            {
                "year": 2000,
                "quarter": 4,
                "sido": "bnd_sido_00_2000_4Q.zip",
                "sigungu": "bnd_sigungu_00_2000_4Q.zip",
                "dong": "bnd_dong_00_2000_4Q.zip",
            },
            {
                "year": 2001,
                "quarter": 4,
                "sido": "bnd_sido_00_2001_4Q.zip",
                "sigungu": "bnd_sigungu_00_2001_4Q.zip",
                "dong": "bnd_dong_00_2001_4Q.zip",
            },
            {
                "year": 2002,
                "quarter": 4,
                "sido": "bnd_sido_00_2002_4Q.zip",
                "sigungu": "bnd_sigungu_00_2002_4Q.zip",
                "dong": "bnd_dong_00_2002_4Q.zip",
            },
            {
                "year": 2003,
                "quarter": 4,
                "sido": "bnd_sido_00_2003_4Q.zip",
                "sigungu": "bnd_sigungu_00_2003_4Q.zip",
                "dong": "bnd_dong_00_2003_4Q.zip",
            },
            {
                "year": 2004,
                "quarter": 4,
                "sido": "bnd_sido_00_2004_4Q.zip",
                "sigungu": "bnd_sigungu_00_2004_4Q.zip",
                "dong": "bnd_dong_00_2004_4Q.zip",
            },
            {
                "year": 2005,
                "quarter": 4,
                "sido": "bnd_sido_00_2005_4Q.zip",
                "sigungu": "bnd_sigungu_00_2005_4Q.zip",
                "dong": "bnd_dong_00_2005_4Q.zip",
            },
            {
                "year": 2006,
                "quarter": 4,
                "sido": "bnd_sido_00_2006_4Q.zip",
                "sigungu": "bnd_sigungu_00_2006_4Q.zip",
                "dong": "bnd_dong_00_2006_4Q.zip",
            },
            {
                "year": 2007,
                "quarter": 4,
                "sido": "bnd_sido_00_2007_4Q.zip",
                "sigungu": "bnd_sigungu_00_2007_4Q.zip",
                "dong": "bnd_dong_00_2007_4Q.zip",
            },
            {
                "year": 2008,
                "quarter": 4,
                "sido": "bnd_sido_00_2008_4Q.zip",
                "sigungu": "bnd_sigungu_00_2008_4Q.zip",
                "dong": "bnd_dong_00_2008_4Q.zip",
            },
            {
                "year": 2009,
                "quarter": 4,
                "sido": "bnd_sido_00_2009_4Q.zip",
                "sigungu": "bnd_sigungu_00_2009_4Q.zip",
                "dong": "bnd_dong_00_2009_4Q.zip",
            },
            {
                "year": 2010,
                "quarter": 4,
                "sido": "bnd_sido_00_2010_4Q.zip",
                "sigungu": "bnd_sigungu_00_2010_4Q.zip",
                "dong": "bnd_dong_00_2010_4Q.zip",
            },
            {
                "year": 2011,
                "quarter": 4,
                "sido": "bnd_sido_00_2011_4Q.zip",
                "sigungu": "bnd_sigungu_00_2011_4Q.zip",
                "dong": "bnd_dong_00_2011_4Q.zip",
            },
            {
                "year": 2012,
                "quarter": 4,
                "sido": "bnd_sido_00_2012_4Q.zip",
                "sigungu": "bnd_sigungu_00_2012_4Q.zip",
                "dong": "bnd_dong_00_2012_4Q.zip",
            },
            {
                "year": 2013,
                "quarter": 4,
                "sido": "bnd_sido_00_2013_4Q.zip",
                "sigungu": "bnd_sigungu_00_2013_4Q.zip",
                "dong": "bnd_dong_00_2013_4Q.zip",
            },
            {
                "year": 2014,
                "quarter": 4,
                "sido": "bnd_sido_00_2014_4Q.zip",
                "sigungu": "bnd_sigungu_00_2014_4Q.zip",
                "dong": "bnd_dong_00_2014_4Q.zip",
            },
            {
                "year": 2015,
                "quarter": 4,
                "sido": "bnd_sido_00_2015_4Q.zip",
                "sigungu": "bnd_sigungu_00_2015_4Q.zip",
                "dong": "bnd_dong_00_2015_4Q.zip",
            },
            {
                "year": 2016,
                "quarter": 4,
                "sido": "bnd_sido_00_2016_4Q.zip",
                "sigungu": "bnd_sigungu_00_2016_4Q.zip",
                "dong": "bnd_dong_00_2016_4Q.zip",
            },
            {
                "year": 2017,
                "quarter": 4,
                "sido": "bnd_sido_00_2017_4Q.zip",
                "sigungu": "bnd_sigungu_00_2017_4Q.zip",
                "dong": "bnd_dong_00_2017_4Q.zip",
            },
            {
                "year": 2018,
                "quarter": 2,
                "sido": "bnd_sido_00_2018_2Q.zip",
                "sigungu": "bnd_sigungu_00_2018_2Q.zip",
                "dong": "bnd_dong_00_2018_2Q.zip",
            },
            {
                "year": 2018,
                "quarter": 4,
                "sido": "bnd_sido_00_2018_4Q.zip",
                "sigungu": "bnd_sigungu_00_2018_4Q.zip",
                "dong": "bnd_dong_00_2018_4Q.zip",
            },
            {
                "year": 2019,
                "quarter": 2,
                "sido": "bnd_sido_00_2019_2Q.zip",
                "sigungu": "bnd_sigungu_00_2019_2Q.zip",
                "dong": "bnd_dong_00_2019_2Q.zip",
            },
            {
                "year": 2019,
                "quarter": 4,
                "sido": "bnd_sido_00_2019_4Q.zip",
                "sigungu": "bnd_sigungu_00_2019_4Q.zip",
                "dong": "bnd_dong_00_2019_4Q.zip",
            },
            {
                "year": 2020,
                "quarter": 2,
                "sido": "bnd_sido_00_2020_2Q.zip",
                "sigungu": "bnd_sigungu_00_2020_2Q.zip",
                "dong": "bnd_dong_00_2020_2Q.zip",
            },
            {
                "year": 2020,
                "quarter": 4,
                "sido": "bnd_sido_00_2020_4Q.zip",
                "sigungu": "bnd_sigungu_00_2020_4Q.zip",
                "dong": "bnd_dong_00_2020_4Q.zip",
            },
            {
                "year": 2021,
                "quarter": 2,
                "sido": "bnd_sido_00_2021_2Q.zip",
                "sigungu": "bnd_sigungu_00_2021_2Q.zip",
                "dong": "bnd_dong_00_2021_2Q.zip",
            },
            {
                "year": 2021,
                "quarter": 4,
                "sido": "bnd_sido_00_2021_4Q.zip",
                "sigungu": "bnd_sigungu_00_2021_4Q.zip",
                "dong": "bnd_dong_00_2021_4Q.zip",
            },
            {
                "year": 2022,
                "quarter": 2,
                "sido": "bnd_sido_00_2022_2Q.zip",
                "sigungu": "bnd_sigungu_00_2022_2Q.zip",
                "dong": "bnd_dong_00_2022_2Q.zip",
            },
            {
                "year": 2022,
                "quarter": 4,
                "sido": "bnd_sido_00_2022_4Q.zip",
                "sigungu": "bnd_sigungu_00_2022_4Q.zip",
                "dong": "bnd_dong_00_2022_4Q.zip",
            },
            {
                "year": 2023,
                "quarter": 2,
                "sido": "bnd_sido_00_2023_2Q.zip",
                "sigungu": "bnd_sigungu_00_2023_2Q.zip",
                "dong": "bnd_dong_00_2023_2Q.zip",
            },
            {
                "year": 2023,
                "quarter": 4,
                "sido": "bnd_sido_00_2023_4Q.zip",
                "sigungu": "bnd_sigungu_00_2023_4Q.zip",
                "dong": "bnd_dong_00_2023_4Q.zip",
            },
            {
                "year": 2024,
                "quarter": 2,
                "sido": "bnd_sido_00_2024_2Q.zip",
                "sigungu": "bnd_sigungu_00_2024_2Q.zip",
                "dong": "bnd_dong_00_2024_2Q.zip",
            },
            {
                "year": 2025,
                "quarter": 2,
                "sido": "bnd_sido_00_2025_2Q.zip",
                "sigungu": "bnd_sigungu_00_2025_2Q.zip",
                "dong": "bnd_dong_00_2025_2Q.zip",
            },
        ]



if __name__ == "__main__":
    PipelineCollection.build()
