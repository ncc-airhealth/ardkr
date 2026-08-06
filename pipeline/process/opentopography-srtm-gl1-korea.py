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
OpenTopography가 배포하는 SRTM GL1(1 arc-second, 약 30m) 수치표고모델 원본 타일.

## 데이터 개요
- SRTM 임무(2000년 2월)에서 간섭레이더로 촬영해 만든 전 지구 DEM이다.
- OpenTopography는 void-filling을 적용한 SRTM V3를 제공한다.
- 이 컬렉션은 한반도와 주변 1° 타일 29개로 구성된다.

## 사용 시 주의사항
- 고도는 EGM96 지오이드 기준, 단위는 m다.
- 값이 없는 셀은 -32768이다. (분석 전에 nodata를 처리 필요)
- C-band 레이더 특성상 수목·건물 등 지표면 위 객체를 반영한 고도일 수 있다.
- 타일은 3601×3601 격자라 이웃 타일과 경계에서 1px(약 30m) 겹친다.

## 메타데이터 설계
- 시간 범위는 촬영 기간(2000-02-11~22)으로 설정했다.
- Item의 bbox는 타일 이름 기준 1° 셀이다.
- USGS는 공공영역, OpenTopography는 "Not Provided"로 표기해 license는 CC0-1.0으로 결정했다.
- 획득 기록의 DOI(10.5069/G9028PQB)는 Copernicus DEM의 것으로, SRTM Global DOI(10.5069/G9445JDF)로 바로잡았다.
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
    COLLECTION_URL = "https://opentopography.s3.sdsc.edu/raster/SRTM_GL1/SRTM_GL1_srtm"
    DATASET_URL = (
        "https://portal.opentopography.org/datasetMetadata"
        "?otCollectionID=OT.042013.4326.1"
    )
    NASA_SRTM_URL = "https://www2.jpl.nasa.gov/srtm/"
    MEDIA_TYPE_GEOTIFF = "image/tiff; application=geotiff"

    # -- 타일·공간·시간 --
    EPSG = 4326
    PIXEL_SIZE_DEG = 1 / 3600
    EXPECTED_SHAPE = (3601, 3601)  # height, width (이웃 타일과 1px 겹침 포함)
    COLLECTION_BBOX = [124.0, 33.0, 132.0, 39.0]
    TEMPORAL_INTERVAL = ["2000-02-11T00:00:00Z", "2000-02-23T00:00:00Z"]
    TILE_NAME_RE = re.compile(r"^N(?P<lat>\d{2})E(?P<lon>\d{3})\.tif$")
    ASSET_NAMES = [
        "N33E126.tif",
        "N34E125.tif",
        "N34E126.tif",
        "N34E127.tif",
        "N34E128.tif",
        "N34E129.tif",
        "N35E125.tif",
        "N35E126.tif",
        "N35E127.tif",
        "N35E128.tif",
        "N35E129.tif",
        "N36E125.tif",
        "N36E126.tif",
        "N36E127.tif",
        "N36E128.tif",
        "N36E129.tif",
        "N37E124.tif",
        "N37E125.tif",
        "N37E126.tif",
        "N37E127.tif",
        "N37E128.tif",
        "N37E129.tif",
        "N37E130.tif",
        "N37E131.tif",
        "N38E124.tif",
        "N38E125.tif",
        "N38E126.tif",
        "N38E127.tif",
        "N38E128.tif",
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
        "id": "opentopography-srtm-gl1-korea",
        "title": "OpenTopography SRTM GL1 30m DEM (한반도 주변 타일)",
        "keywords": [
            "고도",
            "DEM",
            "SRTM",
            "OpenTopography",
            "지형",
            "수치표고모델",
        ],
        "extent": {
            "spatial": {"bbox": [COLLECTION_BBOX]},
            "temporal": {"interval": [TEMPORAL_INTERVAL]},
        },
        "description": __doc__,

        # core: item asset definition
        "item_assets": {
            "dsm": {
                "title": "SRTM GL1 DEM GeoTIFF",
                "description": (
                    "OpenTopography가 배포하는 SRTM GL1 30m DEM "
                    "1° 타일 원본 GeoTIFF."
                ),
                "type": MEDIA_TYPE_GEOTIFF,
                "roles": ["data"],
            }
        },

        # core: license & references
        "license": "CC0-1.0",
        "providers": [
            {
                "name": "National Aeronautics and Space Administration",
                "roles": ["producer"],
                "url": NASA_SRTM_URL,
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
                "href": "https://doi.org/10.5069/G9445JDF",
                "title": "DOI: OpenTopography SRTM Global collection",
                "rel": "related",
                "type": "text/html",
            },
            {
                "href": "https://doi.org/10.5066/F7PR7TFT",
                "title": "DOI: USGS SRTM 1 Arc-Second Global",
                "rel": "related",
                "type": "text/html",
            },
            {
                "href": "https://www.usgs.gov/data-management/data-licensing",
                "title": "USGS 데이터 라이선스 정책",
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
        "SRTM GL1 원본 보존(변환·모자이크 없음) 결정이 적절한지 확인": True,
        "촬영 기간 기준 temporal·명목 1° bbox(1px 겹침) 설계가 적절한지 확인": True,
        "license(공공영역) 표기 결정이 적절한지 확인": True,
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
        self._verify_metadata_consistency(items)

    def _verify_metadata_consistency(self, items: list[Item]) -> None:
        """사람이 확인할 필요 없이 기계로 검증 가능한 metadata 일관성을 확인한다."""
        if Path(__file__).stem != self.collection.id:
            raise AssertionError(
                f"스크립트 파일명 {Path(__file__).stem} != collection id "
                f"{self.collection.id}"
            )

        start, end = (
            datetime.fromisoformat(value) for value in self.TEMPORAL_INTERVAL
        )
        if self.collection.extent.temporal.intervals != [[start, end]]:
            raise AssertionError(
                f"collection temporal extent가 촬영 기간과 다릅니다: "
                f"{self.collection.extent.temporal.intervals}"
            )

        expected_bbox = {
            self._item_id(name): self._tile_bbox(name) for name in self.ASSET_NAMES
        }
        for item in items:
            if item.properties.get("start_datetime") != self.TEMPORAL_INTERVAL[0]:
                raise AssertionError(
                    f"{item.id}: start_datetime이 촬영 기간과 다릅니다"
                )
            if item.properties.get("end_datetime") != self.TEMPORAL_INTERVAL[1]:
                raise AssertionError(
                    f"{item.id}: end_datetime이 촬영 기간과 다릅니다"
                )
            if item.bbox != expected_bbox[item.id]:
                raise AssertionError(
                    f"{item.id}: item.bbox {item.bbox} != 명목 1° 셀 "
                    f"{expected_bbox[item.id]}"
                )

        hrefs = {link.href for link in self.collection.links}
        if "https://doi.org/10.5069/G9445JDF" not in hrefs:
            raise AssertionError("SRTM Global DOI(10.5069/G9445JDF) link가 없습니다")
        if "https://doi.org/10.5069/G9028PQB" in hrefs:
            raise AssertionError("Copernicus DEM DOI(10.5069/G9028PQB)가 잘못 있습니다")
        if "license" not in {link.rel for link in self.collection.links}:
            raise AssertionError("license link가 없습니다")

    def _add_tile_item(self, asset_name: str) -> None:
        west, south, east, north = self._tile_bbox(asset_name)
        item = Item(
            id=self._item_id(asset_name),
            geometry=self._bbox_polygon([west, south, east, north]),
            bbox=[west, south, east, north],
            datetime=None,
            properties={
                "title": f"SRTM GL1 DEM tile {Path(asset_name).stem}",
                "description": (
                    f"OpenTopography SRTM GL1 V3 1° DEM 타일. 원본 파일명: {asset_name}"
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
            title="SRTM GL1 DEM GeoTIFF",
            description=(
                "OpenTopography S3의 SRTM_GL1_srtm 경로에서 받은 원본 DEM GeoTIFF."
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
        if not self._bounds_within_overlap(
            info["bounds"], [west, south, east, north]
        ):
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
        if not self._bounds_within_overlap(info["bounds"], item.bbox):
            raise AssertionError(
                f"{item.id}: item.bbox {item.bbox} != geotiff bounds {info['bounds']}"
            )

        if asset.ext.proj.code != f"EPSG:{self.EPSG}":
            raise AssertionError(
                f"{item.id}: proj.code {asset.ext.proj.code} != EPSG:{self.EPSG}"
            )
        if asset.ext.proj.shape != list(self.EXPECTED_SHAPE):
            raise AssertionError(f"{item.id}: proj.shape {asset.ext.proj.shape}")
        if asset.ext.proj.transform != info["transform"]:
            raise AssertionError(
                f"{item.id}: proj.transform {asset.ext.proj.transform} "
                f"!= 파일 transform {info['transform']}"
            )
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
    def _bounds_within_overlap(actual: list[float], expected: list[float]) -> bool:
        """SRTM 3601×3601 격자의 1px 경계 겹침을 허용해 bbox를 비교한다."""
        tolerance = 1 / 3600 + 1e-9
        if len(actual) != len(expected):
            return False
        return all(abs(a - e) < tolerance for a, e in zip(actual, expected))

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
        return f"opentopography-srtm-gl1-korea-n{lat:02d}e{lon:03d}"

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
