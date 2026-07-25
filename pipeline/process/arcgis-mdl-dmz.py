# /// script
# dependencies = [
#   "duckdb==1.5.5",
#   "pyarrow==25.0.0",
#   "pystac==1.15.1",
#   "python-dotenv==1.2.2",
#   "geovars[pipeline,catalog] @ git+file:///workspace@95f5254a4aea65eb78a52c6095ba1bb59da4640d#subdirectory=geovars",
# ]
#
# [tool.geovars]
# image = "2026.07.21"
# ///

from __future__ import annotations

from pathlib import Path

import duckdb
import geovars.pipeline as gp
import pystac as ps
from dotenv import load_dotenv

# from geovars.catalog import register_collection_version
# from geovars.pipeline import (
#     multihash_sha256,
#     publish_asset,
#     remote_checksum,
#     s3_path,
# )

load_dotenv()


# ----------------------------------------------------------------------------
# settings - developer configurable
VERSION = "3.0.1"
EXPERIMENTAL = True
PUBLISH_MODE = "local"

# metadata configuration -----------------------------------------------------
ITEM_ID_FMT = "{name}"
ASSET_FMT = "{name}.{suffix}"
DESCRIPTION = """
# 소개
ArcGIS API에서 제공하는 군사분계선(MDL) 및 비무장지대(DMZ) 데이터.

인프라 검증용 겸 실사용 collection이다. 
인프라 검증 대상은 아래와 같다.
- 파이프라인 코드 동작
- S3 호환 스토리지로의 Asset 업로드
- STAC metadata 등록
"""


# define stac collection -----------------------------------------------------
coll = ps.Collection(
    id="arcgis-mdl-dmz",
    title="ArcGIS 군사분계선/비무장지대",
    keywords=["ArcGIS", "MDL", "DMZ", "Military Demarcation Line"],
    description=DESCRIPTION,
    extent=None,
    license="proprietary",
    extra_fields={
        "version": VERSION,
        "experimental": EXPERIMENTAL,
        "deprecated": False,
    },
)

# geovars core extensions
coll.ext.add("version")
coll.ext.add("file")
coll.ext.version.apply(version=VERSION, experimental=EXPERIMENTAL)

# additional extensions
coll.ext.add("table")


# process collection/item/asset ----------------------------------------------

class Processor:

    _con: duckdb.DuckDBPyConnection | None = None

    def run(self) -> None:
        self.build_item_mdl()
        self.build_item_dmz()
        self.upload_asset()
    
    def read_mdl_dmz(self) -> Processor:
        self.con.execute(self.mdl_query)
        self.con.execute(self.dmz_query)
        return self
    
    @property
    def con(self) -> duckdb.DuckDBPyConnection:
        if self._con is None:
            self._con = duckdb.connect()
            self._con.execute("""
            INSTALL spatial;
            INSTALL httpfs;
            LOAD spatial;
            LOAD httpfs;

            SET allow_asterisks_in_http_paths = true;
            SET enable_curl_server_cert_verification = false;
            """)
        return self._con
    
    def mdl_query(self) -> str:
        url = (
            "https://portal.esrikr.com/arcgis/rest/services/Hosted/"
            "KR_MDL_DMZ/FeatureServer/0/"
            "query?"
            "where=1%3D1"
            "&outFields=*"
            "&returnGeometry=true"
            "&f=geojson"
            "&outSR=5179"
        )
        return f"""
        CREATE OR REPLACE TEMP TABLE mdl AS (
            SELECT geom FROM ST_Read('{url}')
        )
        """
    
    def dmz_query(self) -> str:
        url = (
            "https://portal.esrikr.com/arcgis/rest/services/Hosted/"
            "KR_MDL_DMZ/FeatureServer/1/"
            "query?"
            "where=1%3D1"
            "&outFields=*"
            "&returnGeometry=true"
            "&f=geojson"
            "&outSR=5179"
        )
        return f"""
        CREATE OR REPLACE TEMP TABLE dmz AS (
            SELECT geom FROM ST_Read('{url}')
        )
        """
    
    # def build_item(self) -> None:
    #     item = ps.Item(
    #         id=ITEM_ID_FMT.format(name="references"),
    #         geometry=None,
    #         bbox=None,
    #         datetime=datetime.fromisoformat(GENERATED_AT),
    #         properties={},
    #     )

    #     item.ext.add("sci")
    #     item.ext.sci.apply(
    #         publications=[
    #             Publication(doi=ref["doi"], citation=citation(ref))
    #             for ref in self.references
    #         ]
    #     )

    #     asset = pystac.Asset(
    #         href=ASSET_FILENAME,  # R2/S3 key 그대로(self-describing) — 버킷명/엔드포인트는 env(GEOVARS_S3_*)
    #         media_type="application/vnd.apache.parquet",
    #         roles=["data"],
    #     )
    #     item.add_asset(
    #         "references", asset
    #     )  # upload_asset이 checksum을 채우려면 owner가 먼저 있어야 함

    #     self.item = item
    
    # @property
    # def reference_table_columns(self) -> list[dict]:
    #     """논문 서지 데이터 테이블의 열 정의. STAC Table extension 문서 참조.
    #     https://github.com/stac-extensions/table#column-object
    #     https://github.com/stac-extensions/scientific
    #     """
    #     return [
    #         {
    #             "name": "doi",
    #             "description": "논문 DOI",
    #             "type": "string",
    #         },
    #         {
    #             "name": "citation",
    #             "description": "논문 인용 문자열(APA 6th edition)",
    #             "type": "string",
    #         }
    #     ]



#     def upload_asset(self) -> None:
#         """geovars.pipeline.publish_asset()으로 asset을 업로드하고 checksum을 기록한다.

#         Sets:
#             self.checksum: 업로드된 파일의 Multihash(sha2-256).
#         """
#         asset = self.item.assets["references"]
#         self.checksum = publish_asset(
#             asset,
#             ASSET_FILENAME,
#             write=lambda f: pd.DataFrame(self.references).to_parquet(f),
#             mode=PUBLISH_MODE,
#         )
#         print(
#             f"[{COLLECTION_ID}] 업로드 완료(mode={PUBLISH_MODE}): "
#             f"key={ASSET_FILENAME} checksum={self.checksum}"
#         )

#     def evaluate_asset(self) -> None:
#         """업로드한 asset을 재검증한다. checksum이 다르거나 로컬 캐시를 재다운로드했으면 예외를 던진다.

#         local 모드는 R2를 건드리지 않으므로 재검증할 원격 실체가 없다 — 스킵한다.
#         발행 여부의 진실은 항상 `verify_uploaded()`가 마지막에 강제한다.
#         """
#         if PUBLISH_MODE == "local":
#             print(f"[{COLLECTION_ID}] local 모드 — 재검증 스킵(원격 미접촉)")
#             return

#         path = s3_path(ASSET_FILENAME)
#         cache_file = Path(path.fspath)
#         mtime_before = cache_file.stat().st_mtime if cache_file.exists() else None

#         data = path.read_bytes()
#         if multihash_sha256(data) != self.checksum:
#             raise ValueError(
#                 f"재다운로드한 asset의 checksum이 기록값과 다릅니다: key={ASSET_FILENAME}"
#             )

#         mtime_after = cache_file.stat().st_mtime
#         if mtime_before != mtime_after:
#             raise ValueError(
#                 f"asset을 로컬 캐시 대신 재다운로드했습니다: key={ASSET_FILENAME}"
#             )

#         print(f"[{COLLECTION_ID}] 재검증 완료: checksum 일치, 로컬 캐시 히트")

#     def build_collection(self) -> None:
#         """STAC Collection을 구성한다.

#         Sets:
#             self.collection: 구성된 pystac.Collection.
#         """
#         collection = pystac.Collection(
#             id=COLLECTION_ID,
#             title=TITLE,
#             description=DESCRIPTION,
#             extent=pystac.Extent(
#                 spatial=pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
#                 temporal=pystac.TemporalExtent(
#                     [[datetime.fromisoformat(GENERATED_AT), None]]
#                 ),
#             ),
#             license="proprietary",
#         )
#         collection.ext.add("version")
#         collection.ext.version.apply(
#             version=VERSION,
#             experimental=EXPERIMENTAL,
#             deprecated=DEPRECATED,
#         )

#         self.collection = collection

#     def register(self) -> None:
#         """collection에 item을 붙이고 카탈로그에 등록한다."""
#         self.collection.add_item(self.item)
#         register_collection(self.collection, VERSION)
#         print(f"[{COLLECTION_ID}] STAC 등록 완료: version={VERSION}")

#     def verify_uploaded(self) -> None:
#         """asset이 실제로 R2에 발행돼 있는지 mode와 무관하게 항상 강제 확인한다.

#         HEAD로 원격 checksum 메타데이터를 읽어 기록값과 비교한다. local 모드로 돌렸다면
#         R2에 아무것도 안 올라가 있으므로 여기서 반드시 실패한다(의도된 안전장치).
#         """
#         actual = remote_checksum(ASSET_FILENAME)
#         if actual != self.checksum:
#             raise ValueError(
#                 f"[{COLLECTION_ID}] asset이 R2에 발행되지 않았거나 checksum이 다릅니다"
#                 f"(mode={PUBLISH_MODE}): key={ASSET_FILENAME} "
#                 f"expected={self.checksum} actual={actual}"
#             )
#         print(f"[{COLLECTION_ID}] 발행 검증 완료: checksum 일치")




# def citation(ref: dict) -> str:
#     """서지 데이터 한 행을 인용 문자열로 바꾼다."""
#     authors = ref["authors"].replace("; ", ", ")
#     return (
#         f"{authors} ({ref['year']}). {ref['title_ko']}. "
#         f"{ref['venue']}, {ref['volume']}({ref['issue']}), {ref['pages']}. {ref['url']}"
#     )


if __name__ == "__main__":
    Processor().run()
