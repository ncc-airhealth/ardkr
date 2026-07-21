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
"""geovars-references — geovars 프로젝트 관련 연구자료(논문) 서지 collection.

인프라 검증용 겸 실사용 collection: 하드코딩된 서지 데이터를 pandas DataFrame으로 만들어
parquet으로 저장하고, S3 호환 스토리지(GEOVARS_S3_*)에 업로드한 뒤 STAC Collection/Item으로
등록한다. STAC Scientific Citation / Version / File Info extension은 pystac의 공식
extension 클래스로 적용한다.
세부: knowledge/decisions/geovars-references-collection.md, pipeline-architecture.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pystac
from dotenv import load_dotenv
from pystac.extensions.file import FileExtension
from pystac.extensions.scientific import Publication, ScientificExtension
from pystac.extensions.version import VersionExtension

from geovars.catalog import register_collection_version
from geovars.pipeline import s3_cache_path, upload_asset

load_dotenv()


class Processor:
    """collection 하나 = 클래스 하나. 클래스 변수는 collection의 메타데이터만, 데이터
    본문은 프로퍼티로 — 메서드가 처리 단계."""

    COLLECTION_ID = "geovars-references"
    VERSION = "0.1.0"
    GENERATED_AT = datetime(2026, 7, 21, tzinfo=timezone.utc)
    TITLE = "geovars 프로젝트 관련 연구자료"
    DESCRIPTION = (
        "geovars 프로젝트와 관련된 연구자료(논문) 서지 정보. item의 asset은 pandas로 만든 "
        "parquet 테이블(논문별 서지 메타데이터 행)이고, STAC Scientific Citation extension"
        "(sci:publications)으로 인용 정보를 기록한다. 동시에 pipeline 인프라(처리 → S3 업로드 "
        "→ STAC 카탈로그 등록) 전체 경로를 검증하는 용도로도 쓰인다."
    )

    @property
    def references(self) -> list[dict]:
        """하드코딩된 서지 데이터(YAGNI) — 논문이 늘면 이 리스트에 항목을 추가하고
        VERSION을 올려 재실행한다."""
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

    @property
    def asset_key(self) -> str:
        return f"{self.COLLECTION_ID}/version={self.VERSION}/references.parquet"

    def citation(self, ref: dict) -> str:
        authors = ref["authors"].replace("; ", ", ")
        return (
            f"{authors} ({ref['year']}). {ref['title_ko']}. "
            f"{ref['venue']}, {ref['volume']}({ref['issue']}), {ref['pages']}. {ref['url']}"
        )

    def build_parquet(self) -> Path:
        out_path = s3_cache_path(self.asset_key)
        pd.DataFrame(self.references).to_parquet(out_path)
        return out_path

    def build_item(self, checksum: str) -> pystac.Item:
        item = pystac.Item(
            id="references", geometry=None, bbox=None, datetime=self.GENERATED_AT, properties={}
        )

        ScientificExtension.ext(item, add_if_missing=True).publications = [
            Publication(doi=ref["doi"], citation=self.citation(ref)) for ref in self.references
        ]

        asset = pystac.Asset(
            href=self.asset_key,  # R2/S3 key 그대로(self-describing) — 버킷명/엔드포인트는 env(GEOVARS_S3_*)
            media_type="application/vnd.apache.parquet",
            roles=["data"],
        )
        item.add_asset("references", asset)
        FileExtension.ext(item.assets["references"], add_if_missing=True).checksum = checksum

        return item

    def build_collection(self) -> pystac.Collection:
        collection = pystac.Collection(
            id=self.COLLECTION_ID,
            title=self.TITLE,
            description=self.DESCRIPTION,
            extent=pystac.Extent(
                spatial=pystac.SpatialExtent([[-180.0, -90.0, 180.0, 90.0]]),
                temporal=pystac.TemporalExtent([[self.GENERATED_AT, None]]),
            ),
            license="proprietary",
        )
        VersionExtension.ext(collection, add_if_missing=True).version = self.VERSION
        return collection

    def run(self) -> None:
        self.build_parquet()
        checksum = upload_asset(self.asset_key)
        print(f"[{self.COLLECTION_ID}] 업로드 완료: key={self.asset_key} checksum={checksum}")

        item = self.build_item(checksum)
        collection = self.build_collection()
        collection.add_item(item)

        register_collection_version(
            Path(__file__).resolve().parents[2] / "stac-metadata",
            collection,
            self.VERSION,
        )
        print(f"[{self.COLLECTION_ID}] STAC 등록 완료: version={self.VERSION}")


if __name__ == "__main__":
    Processor().run()
