# /// script
# dependencies = [
#   "ardkr[pipeline] @ git+https://github.com/ncc-airhealth/ardkr.git@main#subdirectory=ardkr",
#   "httpx==0.28.1",
#   "pystac[validation]==1.15.2",
#   "rasterio==1.5.0",
#   "tqdm==4.70.0",
# ]
#
# [tool.ardkr]
# image = "2026.07.21"
# ///

"""
OpenTopography가 배포하는 ALOS World 3D 30m(AW3D30) DSM 원본 타일.

## 데이터 개요
- JAXA의 ALOS 위성 PRISM 센서가 2006년부터 2011년까지 촬영한 영상으로 만든 지표면 모델이다.
- 수목·건물 등 지표면 위 객체를 포함하는 DSM이다.
- OpenTopography는 평균(average) 다운샘플링 방식이 적용된 V3.2(Jan 2021)를 제공하고 있다.

## 사용 시 주의사항
- 타일 GeoTIFF에 nodata가 정해져 있지 않다. 데이터가 없는 셀은 따로 표시되지 않으므로 주의한다.
- 음수 고도 값이 실제 지형일 수 있다.
- 이 컬렉션은 한반도와 주변의 1° 타일 29개만 포함한다.
- 각 타일은 1° 셀 하나를 담고, 타일 이름의 숫자는 셀의 SW 모서리 위경도다.
- 시간 범위는 ALOS PRISM 관측 기간을 기준으로 정했다.
- 타일별 정확한 촬영일은 제공되지 않아 Item은 관측 기간을 `start_datetime`/`end_datetime`으로 갖는다.

## 라이선스
- OpenTopography 메타데이터는 Use License를 "Not Provided"로 표시한다. 권리와 이용 조건은 JAXA `Terms of Use of Research Data`를 따른다.
- SPDX 식별자가 없어 `license`는 `proprietary`로 설정했다.
"""
import re
from datetime import UTC, datetime
from pathlib import Path

import httpx
import rasterio
from ardkr.pipeline import CollectionBuilder
from pystac import Collection, Item
from pystac.extensions.raster import DataType, RasterBand, Sampling, Statistics
from pystac.utils import datetime_to_str
from tqdm import tqdm


class PipelineCollection(CollectionBuilder):
    # -- 원천 및 형식 --
    COLLECTION_URL = "https://opentopography.s3.sdsc.edu/raster/AW3D30/AW3D30_global"
    DATASET_URL = (
        "https://portal.opentopography.org/datasetMetadata"
        "?otCollectionID=OT.112016.4326.2"
    )
    JAXA_PRODUCT_URL = "https://www.eorc.jaxa.jp/ALOS/en/dataset/aw3d30/aw3d30_e.htm"
    MEDIA_TYPE_GEOTIFF = "image/tiff; application=geotiff"

    # -- 타일·공간·시간 --
    EPSG = 4326
    PIXEL_SIZE_DEG = 1 / 3600
    EXPECTED_SHAPE = (3600, 3600)  # height, width
    COLLECTION_BBOX = [124.0, 33.0, 132.0, 39.0]
    TEMPORAL_INTERVAL = ["2006-01-01T00:00:00Z", "2011-01-01T00:00:00Z"]
    TILE_NAME_RE = re.compile(
        r"^ALPSMLC30_N(?P<lat>\d{3})E(?P<lon>\d{3})_DSM\.tif$"
    )
    ASSET_NAMES = [
        "ALPSMLC30_N033E126_DSM.tif",
        "ALPSMLC30_N034E125_DSM.tif",
        "ALPSMLC30_N034E126_DSM.tif",
        "ALPSMLC30_N034E127_DSM.tif",
        "ALPSMLC30_N034E128_DSM.tif",
        "ALPSMLC30_N034E129_DSM.tif",
        "ALPSMLC30_N035E125_DSM.tif",
        "ALPSMLC30_N035E126_DSM.tif",
        "ALPSMLC30_N035E127_DSM.tif",
        "ALPSMLC30_N035E128_DSM.tif",
        "ALPSMLC30_N035E129_DSM.tif",
        "ALPSMLC30_N036E125_DSM.tif",
        "ALPSMLC30_N036E126_DSM.tif",
        "ALPSMLC30_N036E127_DSM.tif",
        "ALPSMLC30_N036E128_DSM.tif",
        "ALPSMLC30_N036E129_DSM.tif",
        "ALPSMLC30_N037E124_DSM.tif",
        "ALPSMLC30_N037E125_DSM.tif",
        "ALPSMLC30_N037E126_DSM.tif",
        "ALPSMLC30_N037E127_DSM.tif",
        "ALPSMLC30_N037E128_DSM.tif",
        "ALPSMLC30_N037E129_DSM.tif",
        "ALPSMLC30_N037E130_DSM.tif",
        "ALPSMLC30_N037E131_DSM.tif",
        "ALPSMLC30_N038E124_DSM.tif",
        "ALPSMLC30_N038E125_DSM.tif",
        "ALPSMLC30_N038E126_DSM.tif",
        "ALPSMLC30_N038E127_DSM.tif",
        "ALPSMLC30_N038E128_DSM.tif",
    ]

    COLLECTION_STAC_CONTENT = {
        # schema
        "type": "Collection",
        "stac_version": "1.1.0",
        "stac_extensions": [
            "https://stac-extensions.github.io/projection/v2.0.0/schema.json",
            "https://stac-extensions.github.io/raster/v1.1.0/schema.json",
        ],

        # version
        "version": "3.0.1",
        "experimental": False,

        # core: searchables
        "id": "opentopography-alos-world-3d-30m",
        "title": "OpenTopography ALOS World 3D 30m DSM (한반도 주변 타일)",
        "keywords": [
            "고도",
            "DSM",
            "ALOS",
            "AW3D30",
            "OpenTopography",
            "지형",
            "수치표면모델",
        ],
        "extent": {
            "spatial": {"bbox": [COLLECTION_BBOX]},
            "temporal": {"interval": [TEMPORAL_INTERVAL]},
        },
        "description": __doc__,

        # core: item asset definition
        "item_assets": {
            "dsm": {
                "title": "AW3D30 DSM GeoTIFF",
                "description": (
                    "OpenTopography가 배포하는 ALOS World 3D 30m DSM "
                    "1° 타일 원본 GeoTIFF."
                ),
                "type": MEDIA_TYPE_GEOTIFF,
                "roles": ["data"],
            }
        },

        # core: license & references
        "license": "proprietary",
        "providers": [
            {
                "name": "Japan Aerospace Exploration Agency",
                "roles": ["producer", "licensor"],
                "url": JAXA_PRODUCT_URL,
            },
            {
                "name": "OpenTopography",
                "roles": ["host"],
                "url": DATASET_URL,
            },
        ],
        "links": [
            {
                "href": DATASET_URL,
                "title": "OpenTopography 데이터셋 메타데이터",
                "rel": "via",
                "type": "text/html",
            },
            {
                "href": JAXA_PRODUCT_URL,
                "title": "JAXA AW3D30 제품 설명",
                "rel": "via",
                "type": "text/html",
            },
            {
                "href": "https://doi.org/10.5069/G94M92HB",
                "title": "DOI: ALOS World 3D 30 meter DEM V3.2",
                "rel": "related",
                "type": "text/html",
            },
            {
                "href": (
                    "https://object.cloud.sdsc.edu/v1/AUTH_opentopography/"
                    "www/metadata/AW3D30_Metadata.pdf"
                ),
                "title": "OpenTopography AW3D30 메타데이터 PDF",
                "rel": "describedby",
                "type": "application/pdf",
            },
            {
                "href": "https://earth.jaxa.jp/en/data/policy/",
                "title": "JAXA Terms of Use of Research Data",
                "rel": "license",
                "type": "text/html",
            },
            {
                "href": "https://opentopography.org/usageterms",
                "title": "OpenTopography Terms of Use",
                "rel": "license",
                "type": "text/html",
            },
        ],
    }

    collection = Collection.from_dict(COLLECTION_STAC_CONTENT)
    checklist = {
        "collection id와 파일명이 일치하는지 확인": True,
        "JAXA 약관·OpenTopography DOI·V3.2 출처 표기가 metadata에 반영됐는지 확인": True,
        "한반도 주변 타일 목록(29개)과 bbox가 의도한 범위인지 확인": True,
        "다운로드한 DSM 타일을 QGIS 등에서 위치·값 범위로 확인": True,
        "원본 무수정 보존(변환·모자이크 없음) 결정이 적절한지 확인": True,
    }

    def process(self) -> None:
        created = datetime.now(UTC).replace(microsecond=0)
        self.collection.extra_fields["created"] = datetime_to_str(created)

        for asset_name in tqdm(self.ASSET_NAMES, desc="download tiles"):
            self._add_tile_item(asset_name)

        self._update_collection_spatial_extent()

    def verify_auto(self) -> None:
        items = list(self.collection.get_all_items())
        assert len(items) == len(self.ASSET_NAMES), (
            f"Item 개수 {len(items)} != 예상 {len(self.ASSET_NAMES)}"
        )

        expected_ids = {self._item_id(name) for name in self.ASSET_NAMES}
        actual_ids = {item.id for item in items}
        assert actual_ids == expected_ids, (
            f"Item id 집합이 예상과 다릅니다: {sorted(actual_ids ^ expected_ids)}"
        )

        for item in items:
            self._verify_item(item)

        self._verify_collection_bbox_covers_items(items)

    def _add_tile_item(self, asset_name: str) -> None:
        west, south, east, north = self._tile_bbox(asset_name)
        item = Item(
            id=self._item_id(asset_name),
            geometry=self._bbox_polygon([west, south, east, north]),
            bbox=[west, south, east, north],
            datetime=None,
            properties={
                "title": f"AW3D30 DSM tile {Path(asset_name).stem}",
                "description": (
                    f"OpenTopography AW3D30 V3.2 1° DSM 타일. 원본 파일명: {asset_name}"
                ),
                "start_datetime": self.TEMPORAL_INTERVAL[0],
                "end_datetime": self.TEMPORAL_INTERVAL[1],
            },
        )
        item.ext.add("file")
        self.collection.add_item(item)

        asset = item.pipe.define_asset(
            key="dsm",
            store="private",
            filename=asset_name,
            title="AW3D30 DSM GeoTIFF",
            description=(
                "OpenTopography S3의 AW3D30_global 경로에서 받은 원본 DSM GeoTIFF."
            ),
            roles=["data"],
            media_type=self.MEDIA_TYPE_GEOTIFF,
        )
        self._download_source_tile(asset_name, asset.pipe.path())
        asset.pipe.apply_digest()
        self._apply_raster_metadata(asset, asset_name)

    def _download_source_tile(self, asset_name: str, destination: Path) -> None:
        """OpenTopography S3 객체를 원본 그대로 로컬 cache 경로에 저장한다.

        cache에 이미 파일이 있으면 다시 받지 않는다. cache는 순수 가속
        장치이므로, 지워도 같은 URL에서 같은 바이트를 다시 받는다.
        """
        if destination.is_file() and destination.stat().st_size > 0:
            return

        url = f"{self.COLLECTION_URL}/{asset_name}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".part")

        try:
            with httpx.stream(
                "GET",
                url,
                timeout=httpx.Timeout(60.0, connect=30.0),
                follow_redirects=True,
            ) as response:
                response.raise_for_status()
                with temporary.open("wb") as handle:
                    for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)

        if not destination.is_file() or destination.stat().st_size == 0:
            raise ValueError(f"다운로드 결과가 비었습니다: {url}")

    def _apply_raster_metadata(self, asset, asset_name: str) -> None:
        path = asset.pipe.path()
        info = self._read_geotiff_info(path)
        west, south, east, north = self._tile_bbox(asset_name)

        if info["shape"] != list(self.EXPECTED_SHAPE):
            raise ValueError(
                f"{asset_name}: shape {info['shape']} != {list(self.EXPECTED_SHAPE)}"
            )
        if abs(info["pixel_size_x"] - self.PIXEL_SIZE_DEG) > 1e-12:
            raise ValueError(
                f"{asset_name}: pixel size x {info['pixel_size_x']} "
                f"!= {self.PIXEL_SIZE_DEG}"
            )
        if abs(abs(info["pixel_size_y"]) - self.PIXEL_SIZE_DEG) > 1e-12:
            raise ValueError(
                f"{asset_name}: pixel size y {info['pixel_size_y']} "
                f"!= {self.PIXEL_SIZE_DEG}"
            )
        if not self._bounds_close(info["bounds"], [west, south, east, north]):
            raise ValueError(
                f"{asset_name}: bounds {info['bounds']} != {[west, south, east, north]}"
            )

        asset.ext.add("proj")
        asset.ext.proj.code = f"EPSG:{self.EPSG}"
        asset.ext.proj.shape = info["shape"]
        asset.ext.proj.transform = info["transform"]
        asset.ext.proj.bbox = [round(value, 10) for value in info["bounds"]]

        asset.ext.add("raster")
        band = RasterBand.create(
            data_type=DataType.INT16,
            spatial_resolution=30,
            unit="m",
            sampling=Sampling.AREA,
            statistics=Statistics.create(
                minimum=info["minimum"],
                maximum=info["maximum"],
                mean=info["mean"],
                stddev=info["stddev"],
            ),
            nodata=info["nodata"],
        )
        asset.ext.raster.bands = [band]

    def _read_geotiff_info(self, path: Path) -> dict:
        with rasterio.open(path) as src:
            transform = src.transform
            array = src.read(1, masked=True)
            bounds = src.bounds
            return {
                "shape": [src.height, src.width],
                "transform": [
                    transform.a,
                    transform.b,
                    transform.c,
                    transform.d,
                    transform.e,
                    transform.f,
                ],
                "pixel_size_x": transform.a,
                "pixel_size_y": transform.e,
                "bounds": [
                    float(bounds.left),
                    float(bounds.bottom),
                    float(bounds.right),
                    float(bounds.top),
                ],
                "nodata": src.nodata,
                "minimum": float(array.min()),
                "maximum": float(array.max()),
                "mean": float(array.mean()),
                "stddev": float(array.std()),
                "data_type": src.dtypes[0],
            }

    def _verify_item(self, item: Item) -> None:
        if "dsm" not in item.assets:
            raise AssertionError(f"{item.id}: dsm asset이 없습니다")
        if len(item.assets) != 1:
            raise AssertionError(f"{item.id}: asset 개수 {len(item.assets)} != 1")

        asset = item.assets["dsm"]
        path = asset.pipe.path()
        if not path.is_file():
            raise AssertionError(f"{item.id}: 파일이 없습니다: {path}")
        if path.stat().st_size == 0:
            raise AssertionError(f"{item.id}: 파일이 비었습니다: {path}")

        info = self._read_geotiff_info(path)
        if info["data_type"] != "int16":
            raise AssertionError(f"{item.id}: dtype {info['data_type']} != int16")
        if info["shape"] != list(self.EXPECTED_SHAPE):
            raise AssertionError(
                f"{item.id}: shape {info['shape']} != {list(self.EXPECTED_SHAPE)}"
            )
        if not self._bounds_close(info["bounds"], item.bbox):
            raise AssertionError(
                f"{item.id}: item.bbox {item.bbox} != geotiff bounds {info['bounds']}"
            )

        if asset.ext.proj.code != f"EPSG:{self.EPSG}":
            raise AssertionError(
                f"{item.id}: proj.code {asset.ext.proj.code} != EPSG:{self.EPSG}"
            )
        if asset.ext.proj.shape != list(self.EXPECTED_SHAPE):
            raise AssertionError(f"{item.id}: proj.shape {asset.ext.proj.shape}")
        if not asset.ext.raster.bands:
            raise AssertionError(f"{item.id}: raster.bands가 없습니다")

        band = asset.ext.raster.bands[0]
        if band.data_type != DataType.INT16:
            raise AssertionError(f"{item.id}: raster data_type {band.data_type}")
        if band.unit != "m":
            raise AssertionError(f"{item.id}: raster unit {band.unit}")
        if band.spatial_resolution != 30:
            raise AssertionError(
                f"{item.id}: spatial_resolution {band.spatial_resolution}"
            )

        if asset.ext.file.size is None or asset.ext.file.checksum is None:
            raise AssertionError(f"{item.id}: file digest가 없습니다")

        local = asset.pipe.local_digest()
        expected = asset.pipe.digest()
        if local != expected:
            raise AssertionError(
                f"{item.id}: digest mismatch local={local} meta={expected}"
            )

    def _verify_collection_bbox_covers_items(self, items: list[Item]) -> None:
        minx = min(item.bbox[0] for item in items)
        miny = min(item.bbox[1] for item in items)
        maxx = max(item.bbox[2] for item in items)
        maxy = max(item.bbox[3] for item in items)
        actual = [minx, miny, maxx, maxy]
        if actual != self.COLLECTION_BBOX:
            raise AssertionError(
                f"collection bbox 합집합 {actual} != {self.COLLECTION_BBOX}"
            )
        if self.collection.extent.spatial.bboxes != [self.COLLECTION_BBOX]:
            raise AssertionError(
                "collection spatial extent가 선택 타일 합집합과 다릅니다"
            )

    def _update_collection_spatial_extent(self) -> None:
        items = list(self.collection.get_all_items())
        if not items:
            raise ValueError("Item이 없어 spatial extent를 갱신할 수 없습니다")

        minx = min(item.bbox[0] for item in items)
        miny = min(item.bbox[1] for item in items)
        maxx = max(item.bbox[2] for item in items)
        maxy = max(item.bbox[3] for item in items)
        self.collection.extent.spatial.bboxes = [[minx, miny, maxx, maxy]]

    @staticmethod
    def _bounds_close(actual: list[float], expected: list[float]) -> bool:
        if len(actual) != len(expected):
            return False
        return all(abs(a - e) < 1e-9 for a, e in zip(actual, expected))

    @staticmethod
    def _bbox_polygon(bbox: list[float]) -> dict:
        west, south, east, north = bbox
        return {
            "type": "Polygon",
            "coordinates": [
                [
                    [west, south],
                    [east, south],
                    [east, north],
                    [west, north],
                    [west, south],
                ]
            ],
        }

    @classmethod
    def _item_id(cls, asset_name: str) -> str:
        match = cls.TILE_NAME_RE.match(asset_name)
        if match is None:
            raise ValueError(f"타일 이름 형식이 아닙니다: {asset_name}")
        lat = int(match.group("lat"))
        lon = int(match.group("lon"))
        return f"opentopography-alos-world-3d-30m-n{lat:03d}e{lon:03d}"

    @classmethod
    def _tile_bbox(cls, asset_name: str) -> list[float]:
        match = cls.TILE_NAME_RE.match(asset_name)
        if match is None:
            raise ValueError(f"타일 이름 형식이 아닙니다: {asset_name}")
        south = float(int(match.group("lat")))
        west = float(int(match.group("lon")))
        return [west, south, west + 1.0, south + 1.0]



if __name__ == "__main__":
    PipelineCollection.build()
