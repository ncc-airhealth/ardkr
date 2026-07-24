---
name: pipeline-script-shape
description: Use when deciding file layout, module constants, or the Processor class shape for a pipeline/process/<collection-id>.py script.
---

# pipeline-script-shape

`pipeline/process/<collection-id>.py`의 파일 구조 규칙.
진입점은 [write-pipeline-script](../write-pipeline-script/SKILL.md).

## 파일 구조

- 위치: `pipeline/process/<collection-id>.py`. flat 구조, 버전 디렉터리로 나누지 않는다 — 버전 재현은 git commit provenance로 한다.
- lock: 같은 디렉터리의 `<collection-id>.py.lock`. 손으로 만들지 않고 `pipeline/run.py`가 생성/갱신한다([run-pipeline](../run-pipeline/SKILL.md)).
- **스크립트 간 재사용 금지**: `pipeline/process/*.py`끼리는 서로 import하거나 코드를 공유하지 않는다. 옛 스크립트가 새 스크립트의 변경으로 재현성이 깨지면 안 되기 때문이다 — [minimal-code](../minimal-code/SKILL.md)의 "이미 있는 코드는 재사용" 규칙에 대한 예외다. 공용 로직이 필요하면 `geovars` 패키지로 올리고 git-commit pin으로 소비한다.
- PEP723 헤더: `dependencies`는 `==`로 정확히 고정. `geovars`는 `geovars[<extras>] @ git+file:///workspace@<commit>#subdirectory=geovars`로 pin(필요한 extra만: S3면 `pipeline`, STAC 등록이면 `catalog`). `[tool.geovars] image = "YYYY.MM.DD"`로 시스템 이미지 pin.
- 순서: PEP723 헤더 → `from __future__ import annotations` → import → `load_dotenv()` → 모듈 상수 → `Processor` 클래스 → (있다면) 순수 헬퍼 함수 → `if __name__ == "__main__":`. 별도 모듈 docstring은 두지 않는다 — `DESCRIPTION`이 그 역할을 겸한다.

## 모듈 상수

```python
COLLECTION_ID = "..."   # = 파일명 = collection id
VERSION = "3.0.0"
EXPERIMENTAL = True
DEPRECATED = False
PUBLISH_MODE = "local"  # 아직 미발행 — 실제 R2 발행 시 사람이 "remote"로 flip하고 승인 주석 추가
TITLE = "..."
DESCRIPTION = """
...
"""
ASSET_FILENAME = f"{COLLECTION_ID}/version={VERSION}/....parquet"
GENERATED_AT = "2026-07-21T00:00:00+00:00"  # ISO 8601 문자열
```

- **`VERSION`/`EXPERIMENTAL`/`DEPRECATED`는 필수다.** STAC Version Extension(`pystac.extensions.version.VersionExtension`) 필드 그대로다. `EXPERIMENTAL`/`DEPRECATED`는 `True`/`False`를 항상 명시한다.
  - **`EXPERIMENTAL`의 기본값은 `True`다.** `False`로 바꾸는 건 그 collection을 맡은 **사용자가 명시적으로 승인**해야 한다. 승인 사실은 코드에 남긴다: `EXPERIMENTAL = False  # 사용자 승인: YYYY-MM-DD`. 승인 기록이 없는 `False`는 무효 — 근거 없이 `True`로 되돌린다.
  - Collection에만 적용한다. item은 독립된 버전 성숙도 개념이 없다.
- **`VERSION`은 SemVer(`MAJOR.MINOR.PATCH`)다.** leading zero(`01.2.0` 등) 금지, 이전 발행 버전보다 항상 커야 한다. 이 프로젝트는 팀의 세 번째 세대 개편이다 — 이전 프로젝트에서 그대로 가져온 collection이 아니면 `MAJOR`를 `3`으로 시작한다.
- **`PUBLISH_MODE`도 필수, 같은 승인 패턴이다.** 기본값은 `"local"`(R2를 건드리지 않고 `.cache/s3/<bucket>/<key>`에만 씀 — 업로드→검증→개선 반복이 빠름). `"remote"`로 바꾸는 것은 실제 R2 발행을 **사람이 명시적으로 승인**하는 행위다: `PUBLISH_MODE = "remote"  # 발행 승인: YYYY-MM-DD`. CLI 인자·환경변수가 아니라 모듈 상수다 — 발행 여부는 실행할 때마다 흔들리면 안 된다.
- **날짜/시각 상수는 ISO 8601 문자열로 정의한다.** `datetime` 객체가 필요한 자리에서 `datetime.fromisoformat(GENERATED_AT)`로 변환한다.
- **`DESCRIPTION`이 모듈 docstring을 겸한다.** STAC에 발행되는 공개 설명과, 이 스크립트가 왜 이렇게 짜였는지(참고한 skill 경로 등)를 하나의 문자열로 합친다. 한국어로 쓴다. 여는 `"""` 바로 뒤에 내용을 붙이지 않고 줄바꿈한다.
- **`ASSET_FILENAME`은 기본적으로 완성된 값**(f-string)이다. item을 여러 개 만드는 collection은 `ASSET_FILENAME_TEMPLATE = "{collection_id}/version={version}/{item_id}/{filename}"` 같은 템플릿을 두고 각 item 처리 단계에서 `.format(...)`으로 채운다.
  - **item이 여러 개인 collection은 반드시 `{item_id}` 세그먼트로 asset을 item 단위로 묶는다** — 없으면 서로 다른 item의 동명 파일이 같은 key로 충돌한다.

하드코딩 **데이터**(서지 테이블 등)는 모듈 상수가 아니라 `Processor` 클래스의 `@property`로 두고, 클래스 정의 제일 아래에 둔다:

```python
    @property
    def references(self) -> list[dict]:
        """하드코딩된 서지 데이터.

        논문이 늘면 이 리스트에 항목을 추가하고 VERSION을 올려 재실행한다.
        """
        return [...]
```

메타데이터(상수)와 데이터 본문을 구분한다 — 상수 블록은 "collection이 뭔지" 한눈에 보여주는 자리다.

## Google-style docstring

`pipeline/process/*.py`에만 적용한다(`geovars/` 패키지는 한국어 산문 스타일 유지).

- `Processor` 클래스와 각 메서드, 모듈 헬퍼 함수에 Google-style docstring을 쓴다.
- 각 단계 메서드는 `Sets:` 섹션으로 어떤 `self.` 속성을 채우는지 밝힌다.

## `Processor` 클래스

```python
class Processor:
    """<한 줄 요약>."""

    def run(self) -> None:
        """단계 메서드를 순서대로 호출하는 오케스트레이터."""
        self.build_item()
        self.upload_asset()
        self.evaluate_asset()
        self.build_collection()
        self.register()
        self.verify_uploaded()

    def build_item(self) -> None:
        """STAC Item을 구성하고 asset을 attach한다(아직 업로드 전).

        Sets:
            self.item: 구성된 pystac.Item.
        """
        ...

    # upload_asset / evaluate_asset / build_collection / register / verify_uploaded
    # 세부는 pipeline-publish-verify.

    @property
    def references(self) -> list[dict]:
        """하드코딩 데이터. 단계 메서드보다 아래, 클래스 제일 아래에 둔다."""
        return [...]


if __name__ == "__main__":
    Processor().run()
```

- **`run()`이 메서드 정의 중 최상단이다.** 나머지는 `run()`이 호출하는 순서대로 아래에 둔다.
- **`run()` 본문은 조건·반복 없이 `self.xxx()` 호출만 순서대로 나열한다.**
- **단계 메서드는 결과를 인스턴스 속성에 저장하고, 다음 단계가 그 속성을 읽는다.** 반환값을 `run()`이 지역 변수로 이어받아 다음 메서드 인자로 넘기지 않는다.
- **메서드 이름은 collection마다 자유롭다.** item을 하나만 만드는 collection과 여러 개 만드는 collection은 처리 단계 자체가 다르다 — 이름만 자기서술적이면 충분하다(`pipeline/process/geovars-references.py` vs `pipeline/process/sgis-adm-boundary.py`).
- `self` 상태를 전혀 안 쓰는 순수 로직은 인스턴스 메서드로 두지 않는다 — 아래 "순수 헬퍼 함수".

## 순수 헬퍼 함수

`self` 상태를 읽거나 쓰지 않는 로직은 클래스 메서드가 아니라 모듈 함수로 뺀다.
위치는 `Processor` 클래스 아래, `if __name__ == "__main__":` 위.

```python
def citation(ref: dict) -> str:
    """서지 데이터 한 행을 인용 문자열로 바꾼다."""
    ...
```

Python은 모듈 함수의 정의 순서를 신경 쓰지 않는다 — 읽는 사람은 클래스(핵심 흐름)를 먼저 보고, 필요할 때만 아래로 내려가 헬퍼를 확인한다.
