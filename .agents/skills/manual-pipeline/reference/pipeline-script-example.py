# /// script
# dependencies = [
#   # lock은 resolved commit을 기록한다. 로컬 ardkr/ 수정은 원격 의존성에 자동 반영되지 않는다.
#   "ardkr[pipeline] @ git+https://github.com/ncc-airhealth/ardkr.git@main#subdirectory=ardkr",
#   "pystac[validation]==1.15.2",
# ]
#
# [tool.ardkr]
# image = "2026.07.21"
# ///

"""
<Collection별 pipeline script 초안>
"""

from ardkr.pipeline import CollectionBuilder
from pystac import Collection


# fmt: off
COLLECTION_STAC_CONTENT = {
    # schema
    "type": "Collection",
    "stac_version": "1.1.0",
    "stac_extensions": [],

    # version
    # TODO: collection version으로 교체.
    "version": "<replace-me>",
    "experimental": True,

    # core: searchables
    # TODO: extent.spatial에 조사한 데이터의 WGS 84 bbox로 교체.
    # TODO: extent.temporal에 데이터가 나타내는 시점의 시작·끝을 근거와 함께 입력.
    "id": "<replace-me>",
    "keywords": [],
    "extent": {
        "spatial": {"bbox": [[0.0, 0.0, 0.0, 0.0]]},
        "temporal": {"interval": [[None, None]]},
    },
    "description": __doc__,

    # TODO: 조사 결과에 따라 license, providers, links를 입력.
    "license": "<REPLACE_WITH_LICENSE>",
    "providers": [],
    "links": [],
}
# fmt: on


class PipelineCollection(CollectionBuilder):
    collection = Collection.from_dict(COLLECTION_STAC_CONTENT)
    checklist = {
        "collection id와 파일명이 일치하는지 확인": False,
        "조사한 출처·라이선스·시점·공간 범위를 metadata 설계에 반영": False,
        "입력·실행 환경·재현 조건을 확인": False,
        "생성된 asset을 QGIS 또는 적절한 도구로 확인": False,
    }  # 사람이 확인할 항목을 기록한다.

    def process(self) -> None:
        """원본을 읽어 collection의 item과 asset을 생성."""

    def verify_auto(self) -> None:
        """process()가 만든 결과를 자동 검증."""


if __name__ == "__main__":
    PipelineCollection.build()
