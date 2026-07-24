# /// script
# dependencies = [
#   "python-dotenv==1.2.2",
#   "pystac==1.15.1",
#   "geovars[pipeline,catalog] @ git+file:///workspace@95f5254a4aea65eb78a52c6095ba1bb59da4640d#subdirectory=geovars",
# ]
#
# [tool.geovars]
# image = "2026.07.21"
# ///

from __future__ import annotations

import json
import re
import subprocess
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pystac
from dotenv import load_dotenv
from geovars.catalog import register_collection
from geovars.pipeline import (
    multihash_sha256,
    publish_asset,
    remote_checksum,
    s3_path,
    scratch_dir,
)
from pystac.extensions.file import FileExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.table import Column, TableExtension
from pystac.extensions.version import VersionExtension

load_dotenv()

COLLECTION_ID = "sgis-adm-boundary"
VERSION = "0.1.0"
EXPERIMENTAL = True
DEPRECATED = False
PUBLISH_MODE = (
    "local"  # 아직 미발행 — 실제 R2 발행 시 사람이 "remote"로 flip하고 승인 주석 추가
)
TITLE = "SGIS 센서스용 행정구역 경계(시도/시군구/읍면동)"
DESCRIPTION = """
SGIS(통계지리정보서비스, 국가데이터처 제공)의 센서스용 행정구역 경계 자료 — 시도/시군구/
읍면동 3개 레벨, 1975~2025년 37개 시점(2018년부터 반기 2회 2Q/4Q, 그 이전은 연 1회) 원본
shapefile을 가공 없이 그대로 반영한다. item 1개 = 시점 1개(예: "2023-4Q")이고, 그 안에
sido/sigungu/dong 원본 zip 3개가 asset으로 붙는다. 안내: https://sgis.mods.go.kr/view/pss/dataProvdIntrcn

원본은 시계열적으로 스키마·좌표계·인코딩 표기가 일관되지 않는다. 이 collection은 매 실행마다
각 zip을 직접 열어(ogrinfo) 실제 필드 스키마·좌표계·인코딩 사실을 asset properties에 그대로
기록한다(하드코딩이 아니라 원본에서 그때그때 읽어낸 값):

- `table:columns`/`table:row_count` — 실제 dbf 필드명·타입. 레벨·시기별로 대소문자와 이름
  자체가 다르다(예: sido는 sido_cd/sido_nm, 2000년 시군구는 SIGUNGU_CD/SIGUNGU_NM(필드폭
  254, 이례적), 옛 읍면동은 adm_dr_cd/adm_dr_nm, 최근 읍면동은 ADM_CD/ADM_NM).
- `proj:epsg` — 공식 안내 페이지는 EPSG:5179(UTM-K, GRS80)를 명시하지만 `.prj` 파일 자체는
  2019_4Q부터만 존재한다. asset의 `sgis:epsg_declared`가 false면 파일에 좌표계가 없어 이
  공식 값을 가정한 것이다(실측이 아니라 가정임을 구분해서 봐야 한다).
- `sgis:source_encoding`/`sgis:encoding_verified` — `.cpg`는 2011년부터 간헐적, 2022년부터
  일관 존재한다. 그 전 파일은 GDAL이 dbf 헤더의 LDID 바이트로 인코딩(대개 CP949)을 추정해
  읽는데, 예외 없이 읽혔다고 해서 코드페이지를 제대로 짚었다는 보장은 없다(한글이 조용히
  깨질 수 있음). feature 0의 이름 필드를 실제 한글 비율로 자체 검증한 결과를 남긴다.

라이선스/재배포: SGIS 회원 이용약관 제15조③·제16조는 사전 승낙 없는 복제·변경·출판이나
제3자 제공을 원칙적으로 금지하고, 저작권 정책은 공공누리(KOGL) 제1유형이 부착된 저작물만
자유이용을 허용한다고 안내한다. 이 원본(센서스용 행정구역 경계 자료제공 파일)에 KOGL이
실제로 부착돼 있는지, 공개 재배포가 허용되는지는 자료신청 동의문·담당부서 확인 전까지
미확정이다 — 확인 전에는 공개 재배포를 가정하지 않는다. 그래서 `license`는 SPDX 식별자
대신 `proprietary`를 쓰고, 근거 문서는 `links`(rel=license)로 남긴다. 이 collection의
asset은 geovars 저장소의 자격증명 게이트 뒤에 있어(공개 카탈로그일 뿐 데이터는 비공개 —
knowledge/decisions/catalog-and-access.md) 공개 재배포는 아니지만, 확인 전 상태이므로
팀 외부 공유는 보류한다. 문의(자료제공): 042-481-2246, 2517.

인프라 전제조건: 원본 zip은 사전에 `.cache/pipeline/sgis-adm-boundary/raw/`에 준비돼
있어야 한다 — SGIS 사이트에서 수동으로 내려받아 이 위치에 복사해두는 단계는 자동화돼 있지
않다. S3 호환 스토리지 업로드와 STAC 등록은 geovars 공용 유틸로 처리한다. 세부:
knowledge/decisions/geovars-references-collection.md,
knowledge/decisions/pipeline-architecture.md.
"""
LEVELS = ("sido", "sigungu", "dong")
LEVEL_LABELS = {"sido": "시도", "sigungu": "시군구", "dong": "읍면동"}
ASSUMED_EPSG = (
    5179  # 공식 안내(dataProvdIntrcn)의 좌표계 — .prj 없는 파일에만 가정으로 사용
)
ASSET_FILENAME_TEMPLATE = "{collection_id}/version={version}/{item_id}/{filename}"
LICENSE_LINKS = (
    (
        "https://sgis.mods.go.kr/view/member/clause",
        "SGIS 회원 이용약관(제15조 재배포 제한)",
    ),
    (
        "https://sgis.mods.go.kr/jsp/member/copyright.jsp",
        "SGIS 저작권 정책(공공누리 KOGL 안내)",
    ),
)


class Processor:
    """sgis-adm-boundary collection 처리 오케스트레이터."""

    def run(self) -> None:
        """단계 메서드를 순서대로 호출하는 오케스트레이터."""
        self.build_items()
        self.upload_assets()
        self.evaluate_assets()
        self.build_collection()
        self.register()
        self.verify_uploaded()

    def build_items(self) -> None:
        """시점별 item을 만들고 sido/sigungu/dong 원본 zip을 asset으로 attach한다(업로드 전).

        각 zip은 ogrinfo로 열어 실제 필드 스키마·좌표계·인코딩을 읽고 asset properties에
        그대로 기록한다.

        Sets:
            self.items: 시점 순서로 정렬된 pystac.Item 리스트.
        """
        raw_dir = scratch_dir() / "raw"
        tokens = _discover_tokens(raw_dir)

        items = []
        for token in tokens:
            year, quarter = _parse_token(token)
            level_info = {}
            for level in LEVELS:
                filename = f"bnd_{level}_00_{token}.zip"
                zip_path = raw_dir / filename
                inner_name = _inner_shapefile_name(zip_path)
                info = _inspect_shapefile(zip_path, inner_name)
                name_field = next(
                    f["name"]
                    for f in info["fields"]
                    if f["name"].lower().endswith("_nm")
                )
                sample = _sample_name_value(zip_path, inner_name, name_field)
                info["encoding_verified"] = _is_plausible_hangul(sample)
                info["filename"] = filename
                level_info[level] = info

            representative = level_info["sido"]
            bbox = _reproject_bbox_to_wgs84(
                representative["extent"], epsg_or_assumed(representative["epsg"])
            )

            item = pystac.Item(
                id=token.replace("_", "-"),
                geometry=_bbox_polygon(bbox),
                bbox=bbox,
                datetime=_snapshot_datetime(year, quarter),
                properties={},
            )

            for level, info in level_info.items():
                asset = pystac.Asset(
                    href=ASSET_FILENAME_TEMPLATE.format(
                        collection_id=COLLECTION_ID,
                        version=VERSION,
                        item_id=item.id,
                        filename=info["filename"],
                    ),
                    media_type="application/zip",
                    roles=["data"],
                    title=f"{LEVEL_LABELS[level]} 경계 원본 shapefile(zip, 무가공)",
                )
                item.add_asset(
                    level, asset
                )  # upload_assets가 checksum을 채우려면 owner가 먼저 있어야 함

                table_ext = TableExtension.ext(asset, add_if_missing=True)
                table_ext.columns = [Column(f) for f in info["fields"]]
                table_ext.row_count = info["feature_count"]

                ProjectionExtension.ext(
                    asset, add_if_missing=True
                ).epsg = epsg_or_assumed(info["epsg"])

                asset.extra_fields["sgis:layer_name"] = info["layer_name"]
                asset.extra_fields["sgis:epsg_declared"] = info["epsg_declared"]
                asset.extra_fields["sgis:source_encoding"] = info["source_encoding"]
                asset.extra_fields["sgis:encoding_verified"] = info["encoding_verified"]

            items.append(item)

        self.items = items

    def upload_assets(self) -> None:
        """geovars.pipeline.publish_asset()으로 모든 asset을 원본 바이트 그대로 업로드한다.

        raw_dir의 로컬 파일을 그대로 읽어 쓴다 — 재압축·재인코딩 없음.
        """
        raw_dir = scratch_dir() / "raw"
        for item in self.items:
            for asset in item.assets.values():
                zip_path = raw_dir / Path(asset.href).name
                publish_asset(
                    asset,
                    asset.href,
                    write=lambda f, p=zip_path: f.write(p.read_bytes()),
                    mode=PUBLISH_MODE,
                )
        n_assets = sum(len(item.assets) for item in self.items)
        print(
            f"[{COLLECTION_ID}] 업로드 완료(mode={PUBLISH_MODE}): "
            f"item {len(self.items)}개, asset {n_assets}개"
        )

    def evaluate_assets(self) -> None:
        """업로드한 모든 asset을 재검증한다. checksum 불일치나 캐시 미스는 예외를 던진다.

        local 모드는 R2를 건드리지 않으므로 재검증할 원격 실체가 없다 — 스킵한다.
        발행 여부의 진실은 항상 `verify_uploaded()`가 마지막에 강제한다.
        """
        if PUBLISH_MODE == "local":
            print(f"[{COLLECTION_ID}] local 모드 — 재검증 스킵(원격 미접촉)")
            return

        for item in self.items:
            for asset in item.assets.values():
                key = asset.href
                path = s3_path(key)
                cache_file = Path(path.fspath)
                mtime_before = (
                    cache_file.stat().st_mtime if cache_file.exists() else None
                )

                data = path.read_bytes()
                checksum = FileExtension.ext(asset).checksum
                if multihash_sha256(data) != checksum:
                    raise ValueError(
                        f"재다운로드한 asset의 checksum이 기록값과 다릅니다: key={key}"
                    )

                mtime_after = cache_file.stat().st_mtime
                if mtime_before != mtime_after:
                    raise ValueError(
                        f"asset을 로컬 캐시 대신 재다운로드했습니다: key={key}"
                    )

        n_assets = sum(len(item.assets) for item in self.items)
        print(
            f"[{COLLECTION_ID}] 재검증 완료: asset {n_assets}개 checksum 일치, 로컬 캐시 히트"
        )

    def build_collection(self) -> None:
        """STAC Collection을 구성한다. extent는 모든 item의 실제 bbox/datetime에서 계산한다.

        Sets:
            self.collection: 구성된 pystac.Collection.
        """
        bboxes = [item.bbox for item in self.items]
        spatial_extent = [
            min(b[0] for b in bboxes),
            min(b[1] for b in bboxes),
            max(b[2] for b in bboxes),
            max(b[3] for b in bboxes),
        ]
        datetimes = [item.datetime for item in self.items]

        collection = pystac.Collection(
            id=COLLECTION_ID,
            title=TITLE,
            description=DESCRIPTION,
            extent=pystac.Extent(
                spatial=pystac.SpatialExtent([spatial_extent]),
                temporal=pystac.TemporalExtent([[min(datetimes), max(datetimes)]]),
            ),
            license="proprietary",
            providers=[
                pystac.Provider(
                    name="국가데이터처(SGIS 통계지리정보서비스)",
                    roles=["producer", "licensor"],
                    url="https://sgis.mods.go.kr/view/index",
                )
            ],
        )
        for href, title in LICENSE_LINKS:
            collection.add_link(pystac.Link(rel="license", target=href, title=title))

        version_ext = VersionExtension.ext(collection, add_if_missing=True)
        version_ext.version = VERSION
        version_ext.experimental = EXPERIMENTAL
        version_ext.deprecated = DEPRECATED

        self.collection = collection

    def register(self) -> None:
        """collection에 모든 item을 붙이고 카탈로그에 등록한다."""
        for item in self.items:
            self.collection.add_item(item)
        register_collection(self.collection, VERSION)
        print(
            f"[{COLLECTION_ID}] STAC 등록 완료: version={VERSION}, item {len(self.items)}개"
        )

    def verify_uploaded(self) -> None:
        """모든 asset이 실제로 R2에 발행돼 있는지 mode와 무관하게 항상 강제 확인한다.

        HEAD로 원격 checksum 메타데이터를 읽어 기록값과 비교한다. local 모드로 돌렸다면
        R2에 아무것도 안 올라가 있으므로 여기서 반드시 실패한다(의도된 안전장치) — 이
        collection이 "발행됨"이라고 주장하려면 PUBLISH_MODE를 "remote"로 flip해 실제
        업로드를 거쳐야 한다.
        """
        problems = []
        for item in self.items:
            for asset in item.assets.values():
                key = asset.href
                expected = FileExtension.ext(asset).checksum
                actual = remote_checksum(key)
                if actual != expected:
                    problems.append(f"key={key} expected={expected} actual={actual}")

        if problems:
            raise ValueError(
                f"[{COLLECTION_ID}] {len(problems)}개 asset이 R2에 발행되지 않았거나 "
                f"checksum이 다릅니다(mode={PUBLISH_MODE}):\n" + "\n".join(problems)
            )
        n_assets = sum(len(item.assets) for item in self.items)
        print(f"[{COLLECTION_ID}] 발행 검증 완료: asset {n_assets}개 R2 checksum 일치")


def epsg_or_assumed(epsg: int | None) -> int:
    """파일에 좌표계가 없으면 공식 안내값(ASSUMED_EPSG)으로 대체한다."""
    return epsg or ASSUMED_EPSG


def _discover_tokens(raw_dir: Path) -> list[str]:
    """sido/sigungu/dong 파일명에서 공통 시점 토큰(예: "2023_4Q", "1995") 집합을 찾는다.

    세 레벨의 시점 집합이 다르면(한쪽에만 있는 시점) 조용히 무시하지 않고 예외로 알린다.
    """
    if not raw_dir.is_dir():
        raise FileNotFoundError(
            f"원본 zip 디렉토리가 없습니다: {raw_dir} — SGIS에서 내려받은 zip을 미리 복사해두세요."
        )

    per_level: dict[str, set[str]] = {}
    for level in LEVELS:
        prefix, suffix = f"bnd_{level}_00_", ".zip"
        per_level[level] = {
            p.name.removeprefix(prefix).removesuffix(suffix)
            for p in raw_dir.glob(f"{prefix}*{suffix}")
        }

    union = set.union(*per_level.values())
    common = set.intersection(*per_level.values())
    if common != union:
        missing = {
            level: sorted(union - toks)
            for level, toks in per_level.items()
            if union - toks
        }
        raise ValueError(f"레벨 간 시점 불일치(일부 레벨에만 존재하는 시점): {missing}")
    if not common:
        raise FileNotFoundError(f"{raw_dir}에서 원본 zip을 찾지 못했습니다.")

    return sorted(common, key=_token_sort_key)


def _token_sort_key(token: str) -> tuple[int, int]:
    year, quarter = _parse_token(token)
    month = {"2Q": 6, "4Q": 12}.get(quarter, 12)
    return (year, month)


def _parse_token(token: str) -> tuple[int, str | None]:
    """ "2023_4Q" -> (2023, "4Q"), "1995" -> (1995, None)."""
    match = re.fullmatch(r"(\d{4})(?:_(\dQ))?", token)
    if not match:
        raise ValueError(f"인식할 수 없는 시점 토큰: {token}")
    year_str, quarter = match.groups()
    return int(year_str), quarter


def _snapshot_datetime(year: int, quarter: str | None) -> datetime:
    """분기 표기를 기준시점 날짜로 바꾼다(2Q=6/30, 4Q 또는 표기 없음=12/31)."""
    month, day = {"2Q": (6, 30)}.get(quarter, (12, 31))
    return datetime(year, month, day, tzinfo=UTC)


def _inner_shapefile_name(zip_path: Path) -> str:
    """zip 안의 .shp 파일명을 찾는다(zip 파일명과 다를 수 있음 — 원본 명명이 일관되지 않음)."""
    with zipfile.ZipFile(zip_path) as zf:
        shp_names = [n for n in zf.namelist() if n.lower().endswith(".shp")]
    if len(shp_names) != 1:
        raise ValueError(
            f"{zip_path.name}: .shp가 {len(shp_names)}개 발견됨(정확히 1개여야 함)"
        )
    return shp_names[0]


def _vsizip_path(zip_path: Path, inner_name: str) -> str:
    """GDAL이 zip 안 파일을 직접 읽도록 하는 /vsizip/ 가상 경로(압축 해제 없음)."""
    return f"/vsizip/{{{zip_path}}}/{inner_name}"


def _inspect_shapefile(zip_path: Path, inner_name: str) -> dict:
    """zip 안 shapefile을 열어 실제 필드 스키마·좌표계·인코딩 사실을 그대로 읽는다(가공 없음)."""
    result = subprocess.run(
        ["ogrinfo", "-json", "-al", "-so", _vsizip_path(zip_path, inner_name)],
        capture_output=True,
        text=True,
        check=True,
    )
    layer = json.loads(result.stdout)["layers"][0]
    geometry_field = layer["geometryFields"][0]
    coordinate_system = geometry_field.get("coordinateSystem")

    epsg = None
    if coordinate_system and "projjson" in coordinate_system:
        crs_json = coordinate_system["projjson"]
        crs_json = crs_json.get("source_crs", crs_json)
        epsg_id = crs_json.get("id") or {}
        epsg = epsg_id.get("code")

    shapefile_meta = layer.get("metadata", {}).get("SHAPEFILE", {})
    return {
        "layer_name": layer["name"],
        "feature_count": layer["featureCount"],
        "fields": [
            {"name": f["name"], "type": f["type"], "width": f.get("width")}
            for f in layer["fields"]
        ],
        "extent": geometry_field["extent"],
        "epsg": epsg,
        "epsg_declared": coordinate_system is not None,
        "source_encoding": shapefile_meta.get("SOURCE_ENCODING"),
    }


def _sample_name_value(zip_path: Path, inner_name: str, field_name: str) -> str | None:
    """인코딩 자체검증용 — feature 0의 이름 필드를 원본 그대로(디코딩만 거쳐) 읽는다."""
    result = subprocess.run(
        ["ogrinfo", "-al", "-fid", "0", _vsizip_path(zip_path, inner_name)],
        capture_output=True,
        text=True,
        check=True,
    )
    pattern = re.compile(
        rf"^\s*{re.escape(field_name)} \([^)]*\) = (.*)$", re.MULTILINE
    )
    match = pattern.search(result.stdout)
    return match.group(1) if match else None


def _is_plausible_hangul(value: str | None) -> bool:
    """읽은 문자열이 실제 한글로 디코딩됐는지 자체 점검한다.

    GDAL이 예외 없이 읽어도 코드페이지를 잘못 짚으면 글자가 깨질 수 있다(예: CP949 바이트를
    UTF-8로 잘못 해석). "에러 없음"을 "정상 디코딩"과 동일시하지 않기 위한 안전장치다.
    """
    if not value:
        return False
    hangul = sum(1 for ch in value if "가" <= ch <= "힣")
    return hangul / len(value) >= 0.5


def _reproject_bbox_to_wgs84(extent: list[float], epsg: int) -> list[float]:
    """네이티브 좌표계 extent(2개 모서리 좌표)를 WGS84 bbox로 변환한다."""
    minx, miny, maxx, maxy = extent
    coords = f"{minx} {miny}\n{maxx} {maxy}\n"
    result = subprocess.run(
        ["gdaltransform", "-s_srs", f"EPSG:{epsg}", "-t_srs", "EPSG:4326"],
        input=coords,
        capture_output=True,
        text=True,
        check=True,
    )
    corners = [line.split() for line in result.stdout.splitlines() if line.strip()]
    lons = sorted(float(c[0]) for c in corners)
    lats = sorted(float(c[1]) for c in corners)
    return [lons[0], lats[0], lons[-1], lats[-1]]


def _bbox_polygon(bbox: list[float]) -> dict:
    """bbox의 사각형 GeoJSON Polygon(실제 행정경계 외곽선이 아니라 bbox 자체)."""
    minx, miny, maxx, maxy = bbox
    return {
        "type": "Polygon",
        "coordinates": [
            [[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]]
        ],
    }


if __name__ == "__main__":
    Processor().run()
