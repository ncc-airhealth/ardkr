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
시기별 대한민국 행정구역 경계(SGIS 센서스용 원본 Shapefile ZIP).

## 데이터 범위
- 시·도, 시·군·구, 읍·면·동 세 단위의 행정구역 경계를 연도·분기별로 담고 있다.
- 각 시점은 해당 경계의 기준일이며, 공간 범위는 대한민국 전역이다.
- 좌표계는 EPSG:5179(UTM-K)다.

## 시점
- 기준일은 파일명이 아니라 원본 DBF에 적힌 `BASE_DATE`/`base_date` 또는 `base_year` 값을 쓴다. 예를 들어 `2023-2Q`는 파일명과 달리 `2023-07-01`이다.
- `base_year`만 있는 자료는 2분기를 6월 30일, 4분기와 1995년 자료를 12월 31일로 정했다.
- 1995년 원본 DBF에는 `base_year=1995`만 있어 월·일이 직접 기록되지 않았고, SGIS 문서도 기준일이 12월 31일 또는 6월 30일로 서로 다르다. 현재 명시된 12월 31일은 추론된 값이다.
- Collection의 temporal extent는 Item 기준일의 최솟값과 최댓값이다. 그 사이 모든 시점에 경계가 존재하거나 유효하다는 뜻은 아니다.

## 가공 범위
- 원본 ZIP의 공간·속성 데이터는 변환·정규화·보정·삭제하지 않은 원본 그대로다.
- 원본 내 좌표계 정보가 확인됐고, projection 확장에 EPSG:5179로 명시했다.

## 주의사항
- 1975·1980·1990년 읍·면·동 경계의 일부 geometry가 자기 자신과 교차한다. 111개 ZIP(총 138,661개 행) 중 읍·면·동 3개에서 12개다. 세부 개수는 1975년 3개, 1980년 4개, 1990년 5개다.
- 이 geometry는 면적·교차·인접성 같은 공간 연산 결과에 영향을 줄 수 있어, 공간 분석 전 유효성을 검토해야 한다.
"""

from datetime import datetime, timezone
import re

import geopandas as gpd
from ardkr.pipeline import CollectionBuilder
from pystac import Asset, Collection, Item
from pystac.utils import datetime_to_str
from shapely.geometry import box
from tqdm import tqdm

SGIS_DATA_URL = "https://sgis.mods.go.kr/view/pss/openDataIntrcn"
SGIS_PROVISION_URL = "https://sgis.mods.go.kr/view/pss/dataProvdIntrcn"
SGIS_COPYRIGHT_URL = "https://sgis.mods.go.kr/jsp/member/copyright.jsp"
SOUTH_KOREA_BBOX = [124.0, 33.0, 132.0, 39.0]
SOUTH_KOREA_BBOX_GEOM = box(*SOUTH_KOREA_BBOX)

ITEM_ASSET_INFO = {
    "sido": {
        "title": "시도 경계",
        "description": "SGIS가 제공한 시도 단위 Shapefile ZIP.",
        "type": "application/zip",
    },
    "sigungu": {
        "title": "시군구 경계",
        "description": "SGIS가 제공한 시군구 단위 Shapefile ZIP.",
        "type": "application/zip",
    },
    "dong": {
        "title": "읍면동 경계",
        "description": "SGIS가 제공한 읍면동 단위 Shapefile ZIP.",
        "type": "application/zip",
    },
}


# fmt: off
COLLECTION_STAC_CONTENT = {

    # schema
    "type": "Collection",
    "stac_version": "1.1.0",
    "stac_extensions": [
        "https://stac-extensions.github.io/table/v1.2.0/schema.json",
        "https://stac-extensions.github.io/projection/v2.0.0/schema.json",
    ],

    # version
    "version": "3.0.1",
    "experimental": False,

    # core: searchables
    "id": "sgis-adm-bnd",
    "title": "SGIS 센서스용 행정구역 경계",
    "keywords": ["행정구역 경계", "센서스", "시도", "시군구", "읍면동", "SGIS"],
    "extent": {
        "spatial": {"bbox": [SOUTH_KOREA_BBOX]},
        "temporal": {
            "interval": [["1975-12-31T00:00:00Z", "2025-06-30T00:00:00Z"]]
        },
    },
    "description": __doc__,

    # core: item asset definition
    "item_assets": {
        key: {
            **value,
            "roles": ["data"],
        }
        for key, value in ITEM_ASSET_INFO.items()
    },


    # core: license & references
    "license": "proprietary",
    "providers": [
        {
            "name": "국가데이터처(통계지리정보서비스)",
            "roles": ["producer", "licensor", "host"],
            "url": "https://sgis.mods.go.kr/",
        },
    ],
    "links": [
        {
            "href": SGIS_DATA_URL,
            "title": "SGIS 자료제공 목록",
            "rel": "via",
            "type": "text/html",
        },
        {
            "href": SGIS_PROVISION_URL,
            "title": "SGIS 자료제공 안내",
            "rel": "describedby",
            "type": "text/html",
        },
        {
            "href": SGIS_COPYRIGHT_URL,
            "title": "SGIS 저작권 정책",
            "rel": "license",
            "type": "text/html",
        },
    ]
}
# fmt: on


class PipelineCollection(CollectionBuilder):
    collection = Collection.from_dict(COLLECTION_STAC_CONTENT)
    checklist = {
        "데이터를 QGIS로 로드하여 베이스맵과의 위치 일관성을 확인": True,
        "원본 aggregate ZIP과 inner ZIP의 관계 및 무수정 보존을 확인": True,
        "base_year만 있는 자료의 기준일 해석 근거와 한계를 확인": True,
        "SGIS 신청 자료의 이용조건과 공공누리 표시 여부를 확인": True,
        "입력 cache와 수동 획득 파일이 같은지 확인": True,
    }
    item_id_fmt = "sgis-adm-bnd-{year}-{quarter}q"
    default_epsg = 5179  # https://sgis.mods.go.kr/view/pss/dataProvdIntrcn

    def process(self) -> None:
        created = datetime.now(timezone.utc).replace(microsecond=0)
        self.collection.extra_fields["created"] = datetime_to_str(created)
        self._add_items()
        self._add_thumbnail_asset()
        self._update_collection_extent()

    def verify_auto(self) -> None:
        self._verify_item_count()
        self._verify_item_has_3_assets()
        self._verify_item_datetime()
        self._verify_bnd_asset_range()
        self._verify_thumbnail_asset()

    def _add_items(self):
        """FILES_INFO 기준으로 item 생성."""
        for item_group in tqdm(self.files_info, desc="adding items"):
            self._bnd_group_to_item(item_group)

    def _bnd_group_to_item(self, item_group: dict):
        """연·분기 그룹을 STAC item과 sido/sigungu/dong asset으로 등록."""
        quarter = item_group["quarter"]
        item = Item(
            id=self._item_id(item_group),
            geometry=None,
            bbox=list(SOUTH_KOREA_BBOX),
            # PySTAC requires a datetime at construction time. It is replaced
            # with the common DBF-derived date after all three assets are read.
            datetime=datetime(1970, 1, 1, tzinfo=timezone.utc),
            properties={},
        )
        item.ext.add("file")
        self.collection.add_item(item)

        source_datetimes = []
        for level in ITEM_ASSET_INFO:
            asset_info = ITEM_ASSET_INFO[level]
            asset = item.pipe.define_asset(
                key=level,
                store="private",
                filename=item_group[level],
                title=asset_info["title"],
                description=asset_info["description"],
                roles=["data"],
                media_type=asset_info["type"],
            )
            source_datetimes.append(
                self._update_bnd_asset_metadata(asset, quarter)
            )

        if len(set(source_datetimes)) != 1:
            raise ValueError(
                f"{item.id}: level별 기준일이 일치하지 않습니다: "
                f"{source_datetimes}"
            )
        item.datetime = source_datetimes[0]

    def _item_id(self, item_group: dict) -> str:
        quarter = item_group["quarter"]
        quarter_id = 0 if quarter is None else quarter
        return self.item_id_fmt.format(
            year=item_group["year"], quarter=quarter_id
        )

    def _update_bnd_asset_metadata(
        self, asset: Asset, quarter: int | None
    ) -> datetime:
        """shapefile zip을 읽어 table·proj·encoding 메타를 asset에 적는다."""
        local_path = asset.pipe.path()
        if not local_path.is_file():
            raise FileNotFoundError(
                f"입력 ZIP이 없습니다: {local_path}. "
                "SGIS에서 받은 inner ZIP을 해당 private cache에 배치하세요."
            )
        vsi = f"/vsizip/{local_path.resolve()}"
        encoding, table = self._read_with_encoding(vsi)
        source_datetime = self._source_datetime_from_table(table, quarter)

        asset.pipe.apply_digest()
        asset.ext.add("table")
        asset.ext.table.columns = [
            {
                "name": name,
                "type": str(dtype),
                **(
                    {"description": self._column_description(name)}
                    if self._column_description(name) is not None
                    else {}
                ),
            }
            for name, dtype in table.dtypes.items()
        ] + [
            {
                "name": "geometry",
                "type": "geometry",
                "description": "행정구역 경계 geometry.",
            }
        ]
        asset.ext.table.row_count = len(table)
        asset.ext.table.primary_geometry = "geometry"
        asset.ext.table.storage_options = {"encoding": encoding}
        asset.ext.add("proj")
        asset.ext.proj.code = f"EPSG:{self.default_epsg}"
        return source_datetime

    @staticmethod
    def _column_description(name: str) -> str | None:
        if name.lower() == "base_date":
            return "원본 DBF가 기록한 경계 기준일(YYYYMMDD)."
        if name.lower() == "base_year":
            return "원본 DBF가 기록한 경계 기준연도."
        return None

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

    def _source_datetime_from_table(
        self, table, quarter: int | None
    ) -> datetime:
        """DBF의 기준일 필드로 Item datetime을 결정한다."""
        columns = {name.lower(): name for name in table.columns}
        if "base_date" in columns:
            column = columns["base_date"]
            values = [self._parse_base_date(value) for value in table[column]]
            if not values or any(value is None for value in values):
                raise ValueError(f"유효한 BASE_DATE가 없습니다: {column}")
            if len(set(values)) != 1:
                raise ValueError(f"BASE_DATE 값이 여러 개입니다: {set(values)}")
            return values[0]

        if "base_year" not in columns:
            raise ValueError("BASE_DATE/base_date 또는 base_year 필드가 없습니다")

        column = columns["base_year"]
        years = [self._parse_base_year(value) for value in table[column]]
        if not years or len(set(years)) != 1:
            raise ValueError(f"base_year 값이 여러 개입니다: {set(years)}")

        if quarter == 2:
            month, day = 6, 30
        elif quarter == 4 or quarter is None:
            month, day = 12, 31
        else:
            raise NotImplementedError(f"지원하지 않는 분기: {quarter}")
        return datetime(years[0], month, day, tzinfo=timezone.utc)

    @staticmethod
    def _parse_base_date(value) -> datetime | None:
        text = str(value).strip()
        if text.lower() in {"", "nan", "none"}:
            return None
        if re.fullmatch(r"\d{8}\.0+", text):
            text = text.split(".", 1)[0]
        try:
            return datetime.strptime(text, "%Y%m%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError as exc:
            raise ValueError(f"BASE_DATE 형식이 아닙니다: {value!r}") from exc

    @staticmethod
    def _parse_base_year(value) -> int:
        text = str(value).strip()
        if text.lower() in {"", "nan", "none"}:
            raise ValueError(f"base_year가 비어 있습니다: {value!r}")
        if re.fullmatch(r"\d{4}\.0+", text):
            text = text.split(".", 1)[0]
        if not re.fullmatch(r"\d{4}", text):
            raise ValueError(f"base_year 형식이 아닙니다: {value!r}")
        return int(text)

    def _add_thumbnail_asset(self):
        """collection thumbnail asset을 등록."""
        asset = self.collection.pipe.define_asset(
            key="thumbnail",
            store="open",
            filename="thumbnail.webp",
            title="미리보기",
            description="SGIS 행정구역 경계 데이터의 미리보기 이미지.",
            roles=["thumbnail"],
            media_type="image/webp",
        )
        path = asset.pipe.path()
        if not path.is_file():
            raise FileNotFoundError(f"thumbnail 파일이 없습니다: {path}")
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

        ordered = sorted(datetimes)
        self.collection.extent.temporal.intervals = [
            [ordered[0], ordered[-1]]
        ]

    def _verify_item_count(self) -> None:
        items = list(self.collection.get_all_items())
        if len(items) != len(self.files_info):
            raise AssertionError(
                f"Item 개수 {len(items)} != 예상 개수 {len(self.files_info)}"
            )

    def _verify_item_datetime(self) -> None:
        """각 Item datetime이 세 원본 DBF의 기준일과 일치하는지 확인한다."""
        groups = {self._item_id(group): group for group in self.files_info}
        for item in self.collection.get_all_items():
            group = groups.get(item.id)
            if group is None:
                raise AssertionError(f"예상하지 않은 Item입니다: {item.id}")

            source_datetimes = []
            for asset in item.assets.values():
                encoding = asset.ext.table.storage_options["encoding"]
                table = gpd.read_file(
                    asset.pipe.path(),
                    encoding=encoding,
                    ignore_geometry=True,
                )
                source_datetimes.append(
                    self._source_datetime_from_table(table, group["quarter"])
                )

            if len(set(source_datetimes)) != 1:
                raise AssertionError(
                    f"{item.id}: 원본 asset 기준일이 일치하지 않습니다: "
                    f"{source_datetimes}"
                )
            if item.datetime != source_datetimes[0]:
                raise AssertionError(
                    f"{item.id}: Item datetime={item.datetime!r}, "
                    f"DBF 기준일={source_datetimes[0]!r}"
                )

    def _verify_item_has_3_assets(self):
        """각 item의 asset이 3개인지 확인한다."""
        for item in self.collection.get_all_items():
            if len(item.assets) != 3:
                raise AssertionError(f"{item.id}: asset 개수 {len(item.assets)} != 3")
            if item.datetime is None:
                raise AssertionError(f"{item.id}: datetime이 없습니다")

    def _verify_bnd_asset_range(self):
        """geometry의 필수 상태와 대한민국 범위를 확인한다.

        invalid geometry는 원본 품질 한계로 description에 기록했으므로
        보정하거나 검증 실패로 처리하지 않는다.
        """
        items = self.collection.get_all_items()
        for item in tqdm(items, desc="verify boundary asset_range"):
            for key, asset in item.assets.items():
                encoding = asset.ext.table.storage_options["encoding"]
                boundary = gpd.read_file(asset.pipe.path(), encoding=encoding)
                if boundary.empty:
                    raise AssertionError(f"{item.id}/{key}: geometry가 비었습니다")
                if boundary.geometry.isna().any():
                    raise AssertionError(f"{item.id}/{key}: 빈 geometry가 있습니다")
                if boundary.geometry.is_empty.any():
                    raise AssertionError(f"{item.id}/{key}: empty geometry가 있습니다")
                invalid_count = int((~boundary.geometry.is_valid).sum())
                if invalid_count:
                    print(
                        f"{item.id}/{key}: 원본에 유효하지 않은 geometry "
                        f"{invalid_count}개가 있습니다. 품질 한계로 기록하고 "
                        "계속합니다."
                    )

                if boundary.crs is None:
                    boundary = boundary.set_crs(epsg=self.default_epsg)
                elif boundary.crs.to_epsg() != self.default_epsg:
                    raise AssertionError(
                        f"{item.id}/{key}: CRS가 EPSG:{self.default_epsg}가 아닙니다: "
                        f"{boundary.crs}"
                    )

                asset_extent = boundary.to_crs(epsg=4326).total_bounds
                if not SOUTH_KOREA_BBOX_GEOM.covers(box(*asset_extent)):
                    raise AssertionError(
                        f"{item.id}/{key}: asset extent {asset_extent} "
                        f"is outside SOUTH_KOREA_BBOX {SOUTH_KOREA_BBOX}"
                    )

    def _verify_thumbnail_asset(self) -> None:
        path = self.collection.assets["thumbnail"].pipe.path()
        if not path.is_file():
            raise AssertionError(f"thumbnail 파일이 없습니다: {path}")
        if path.stat().st_size == 0:
            raise AssertionError(f"thumbnail 파일이 비어 있습니다: {path}")

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
