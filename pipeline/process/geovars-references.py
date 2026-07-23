# /// script
# dependencies = [
#   "pandas==3.0.3",
#   "pyarrow==25.0.0",
#   "python-dotenv==1.2.2",
#   "geovars[pipeline,catalog] @ git+file:///workspace@2ccf5e217cd339caf0885c0ad93fb3b69b27590a#subdirectory=geovars",
# ]
#
# [tool.geovars]
# image = "2026.07.21"
# ///

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import pystac
from dotenv import load_dotenv
from geovars.catalog import register_collection_version
from geovars.pipeline import multihash_sha256, publish_asset, s3_path
from pystac.extensions.scientific import Publication, ScientificExtension
from pystac.extensions.version import VersionExtension

load_dotenv()

COLLECTION_ID = "geovars-references"
VERSION = "0.1.0"
EXPERIMENTAL = True
DEPRECATED = False
TITLE = "geovars 프로젝트 관련 연구자료"
DESCRIPTION = """
geovars 프로젝트와 관련된 연구자료(논문) 서지 정보. item의 asset은 pandas로
만든 parquet 테이블(논문별 서지 메타데이터 행)이고, STAC Scientific Citation extension
(sci:publications)으로 인용 정보를 기록한다.

인프라 검증용 겸 실사용 collection이다 — S3 호환 스토리지(GEOVARS_S3_*) 업로드와 STAC
Collection/Item 등록까지 pipeline 인프라 전체 경로를 이 collection으로 검증한다. STAC
Scientific Citation/Version/File Info extension은 pystac의 공식 extension 클래스로 적용한다.
세부: knowledge/decisions/geovars-references-collection.md, pipeline-architecture.md.
"""
GENERATED_AT = "2026-07-21T00:00:00+00:00"
ASSET_KEY = f"{COLLECTION_ID}/version={VERSION}/references.parquet"


class Processor:
    """geovars-references collection 처리 오케스트레이터."""

    def run(self) -> None:
        """단계 메서드를 순서대로 호출하는 오케스트레이터."""
        self.build_item()
        self.upload_asset()
        self.evaluate_asset()
        self.build_collection()
        self.register()

    def build_item(self) -> None:
        """STAC Item을 구성하고 asset을 attach한다(아직 업로드 전).

        Sets:
            self.item: 구성된 pystac.Item.
        """
        item = pystac.Item(
            id="references",
            geometry=None,
            bbox=None,
            datetime=datetime.fromisoformat(GENERATED_AT),
            properties={},
        )

        ScientificExtension.ext(item, add_if_missing=True).publications = [
            Publication(doi=ref["doi"], citation=citation(ref))
            for ref in self.references
        ]

        asset = pystac.Asset(
            href=ASSET_KEY,  # R2/S3 key 그대로(self-describing) — 버킷명/엔드포인트는 env(GEOVARS_S3_*)
            media_type="application/vnd.apache.parquet",
            roles=["data"],
        )
        item.add_asset(
            "references", asset
        )  # upload_asset이 checksum을 채우려면 owner가 먼저 있어야 함

        self.item = item

    def upload_asset(self) -> None:
        """geovars.pipeline.publish_asset()으로 asset을 업로드하고 checksum을 기록한다.

        Sets:
            self.checksum: 업로드된 파일의 Multihash(sha2-256).
        """
        asset = self.item.assets["references"]
        self.checksum = publish_asset(
            asset,
            ASSET_KEY,
            write=lambda f: pd.DataFrame(self.references).to_parquet(f),
        )
        print(
            f"[{COLLECTION_ID}] 업로드 완료: key={ASSET_KEY} checksum={self.checksum}"
        )

    def evaluate_asset(self) -> None:
        """업로드한 asset을 재검증한다. checksum이 다르거나 로컬 캐시를 재다운로드했으면 예외를 던진다."""
        path = s3_path(ASSET_KEY)
        cache_file = Path(path.fspath)
        mtime_before = cache_file.stat().st_mtime if cache_file.exists() else None

        data = path.read_bytes()
        if multihash_sha256(data) != self.checksum:
            raise ValueError(
                f"재다운로드한 asset의 checksum이 기록값과 다릅니다: key={ASSET_KEY}"
            )

        mtime_after = cache_file.stat().st_mtime
        if mtime_before != mtime_after:
            raise ValueError(
                f"asset을 로컬 캐시 대신 재다운로드했습니다: key={ASSET_KEY}"
            )

        print(f"[{COLLECTION_ID}] 재검증 완료: checksum 일치, 로컬 캐시 히트")

    def build_collection(self) -> None:
        """STAC Collection을 구성한다.

        Sets:
            self.collection: 구성된 pystac.Collection.
        """
        collection = pystac.Collection(
            id=COLLECTION_ID,
            title=TITLE,
            description=DESCRIPTION,
            extent=pystac.Extent(
                spatial=pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
                temporal=pystac.TemporalExtent(
                    [[datetime.fromisoformat(GENERATED_AT), None]]
                ),
            ),
            license="proprietary",
        )
        version_ext = VersionExtension.ext(collection, add_if_missing=True)
        version_ext.version = VERSION
        version_ext.experimental = EXPERIMENTAL
        version_ext.deprecated = DEPRECATED

        self.collection = collection

    def register(self) -> None:
        """collection에 item을 붙이고 카탈로그에 등록한다."""
        self.collection.add_item(self.item)
        register_collection_version(
            Path(__file__).resolve().parents[2] / "stac-metadata",
            self.collection,
            VERSION,
        )
        print(f"[{COLLECTION_ID}] STAC 등록 완료: version={VERSION}")

    @property
    def references(self) -> list[dict]:
        """하드코딩된 서지 데이터.

        논문이 늘면 이 리스트에 항목을 추가하고 VERSION을 올려 재실행한다.
        """
        return [
            {
                "title_ko": "환경의 건강 영향 연구를 위한 공간지리정보 데이터 파이프라인-자료활용의 제한점과 극복방안-",
                "title_en": "Geospatial Data Pipeline to Study the Health Effects of Environments -Limitations and Solutions-",
                "authors": "김원경; 정고은; 손동욱; 김선영",
                "year": 2024,
                "venue": "한국지리정보학회지",
                "volume": 27,
                "issue": 3,
                "pages": "60-75",
                "doi": "10.11108/kagis.2024.27.3.060",
                "url": "https://doi.org/10.11108/kagis.2024.27.3.060",
                "keywords": "Relational Database; Data Pipeline; Epidemiology; Geographical Variables; Environmental Risk Factors",
                "added_at": "2026-07-21",
            },
        ]


def citation(ref: dict) -> str:
    """서지 데이터 한 행을 인용 문자열로 바꾼다."""
    authors = ref["authors"].replace("; ", ", ")
    return (
        f"{authors} ({ref['year']}). {ref['title_ko']}. "
        f"{ref['venue']}, {ref['volume']}({ref['issue']}), {ref['pages']}. {ref['url']}"
    )


if __name__ == "__main__":
    Processor().run()
