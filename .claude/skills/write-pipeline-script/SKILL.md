---
name: write-pipeline-script
description: >-
  Use when writing or editing pipeline/process/<collection-id>.py processing
  scripts, adding a new collection, or refactoring an existing process script.
---

# write-pipeline-script

`pipeline/process/<collection-id>.py`는 파일명이 곧 collection id인 flat 처리 스크립트다.
사람이 열어서 검토하는 게 핵심 목적이라, 다른 어떤 코드보다 가독성을 우선한다. 이 스킬은
그 규칙을 모은 것이다. 세부 근거는
[/decisions/pipeline-architecture.md](../../../knowledge/decisions/pipeline-architecture.md),
[/decisions/geovars-references-collection.md](../../../knowledge/decisions/geovars-references-collection.md),
[/decisions/cloudpathlib-cache-pattern.md](../../../knowledge/decisions/cloudpathlib-cache-pattern.md),
[/decisions/versioning-and-corrections.md](../../../knowledge/decisions/versioning-and-corrections.md).

## 목표 사용자 경험

파일을 열면 이 순서로 읽힌다.

1. 상단 상수(`DESCRIPTION` 포함)를 보고 collection이 뭔지 파악한다.
2. `Processor.run()`을 보고 처리 흐름을 파악한다.
3. 궁금한 처리방식은 `run()`이 호출한 메서드의 정의를 따라가며 확인한다.

## 시작 전

- `recall-knowledge`로 다루려는 기관·데이터셋 관련 과거 결정을 먼저 조회한다.
- 비슷한 기존 스크립트를 참고하되, **코드를 공유하거나 import하지 않는다.** 아래 "스크립트 간
  재사용 금지"를 본다.

## 파일 구조

- 위치: `pipeline/process/<collection-id>.py`. flat 구조이며 버전 디렉터리로 나누지 않는다.
- lock: 같은 디렉터리의 `<collection-id>.py.lock`. 손으로 만들지 않고 `pipeline/run.py`가
  생성/갱신한다.
- PEP723 헤더
  - `dependencies`는 정확한 버전(`==`)으로 고정한다.
  - `geovars`는 git commit pin으로 가져온다: `geovars[<extras>] @ git+file:///workspace@<commit>#subdirectory=geovars`.
    필요한 extra만 선택한다(S3면 `pipeline`, STAC 카탈로그 등록이면 `catalog`).
  - `[tool.geovars] image = "YYYY.MM.DD"`로 시스템 이미지를 pin한다.

  ```python
  # /// script
  # dependencies = [
  #   "python-dotenv==1.2.2",
  #   "geovars[<extras>] @ git+file:///workspace@<commit>#subdirectory=geovars",
  # ]
  #
  # [tool.geovars]
  # image = "YYYY.MM.DD"
  # ///
  ```

  `<commit>`/`<extras>`/버전 값은 자리표시자다 — collection마다 실제 값으로 채운다.
- 헤더 다음은 `from __future__ import annotations`로 시작하는 import 블록, 그다음
  `load_dotenv()` 호출, 그다음 모듈 최상단 상수, 그다음 `Processor` 클래스, 그다음(있다면)
  순수 헬퍼 함수, 마지막에 `if __name__ == "__main__":` 순서로 둔다. 별도 모듈 docstring은
  두지 않는다 — `DESCRIPTION`이 그 역할을 겸한다(아래 참고).

## 모듈 상수

collection 메타데이터는 전부 클래스 밖 모듈 상수로 둔다. 스크립트 하나가 collection 하나이므로,
클래스로 감쌀 이유가 없다.

```python
COLLECTION_ID = "..."   # = 파일명 = collection id
VERSION = "0.1.0"
EXPERIMENTAL = True
DEPRECATED = False
TITLE = "..."
DESCRIPTION = """..."""
ASSET_KEY = f"{COLLECTION_ID}/version={VERSION}/....parquet"
GENERATED_AT = "2026-07-21T00:00:00+00:00"  # ISO 8601 문자열. datetime 객체가 필요하면 datetime.fromisoformat(GENERATED_AT)
```

하드코딩 **데이터**(서지 테이블, 코드북 등 본문 데이터)는 모듈 상수가 아니라 `Processor`
클래스의 `@property`로 두고, 클래스 정의 **제일 아래**(`register()`류 마지막 단계 메서드보다도
아래)에 둔다.

```python
    @property
    def references(self) -> list[dict]:
        """하드코딩된 서지 데이터.

        논문이 늘면 이 리스트에 항목을 추가하고 VERSION을 올려 재실행한다.
        """
        return [...]
```

- 메타데이터(상수)와 데이터 본문을 구분한다. 상수 블록은 "collection이 뭔지" 한눈에 보여주는
  자리라, 길어질 수 있는 데이터 테이블이 섞이면 그 목적이 흐려진다.
- 클래스 제일 아래에 두는 이유는 `run()`이 최상단이라는 규칙과 같다 — 핵심 흐름(`run()`과
  단계 메서드)을 다 보고 나서야 필요하면 내려가 데이터 본문을 확인한다.

- **`VERSION`/`EXPERIMENTAL`/`DEPRECATED`는 필수다.** 셋 다 STAC Version Extension
  (`pystac.extensions.version.VersionExtension`) 필드 그대로이고, collection 유지보수에
  꼭 필요한 신호라 생략을 허용하지 않는다.
  - `EXPERIMENTAL`/`DEPRECATED`는 `Optional[bool]`(pystac 기본값)로 남겨두지 않고 항상
    `True`/`False`를 명시한다. 미지정과 "확실히 아님"이 구분 안 되면 신호로서 의미가 없다.
  - **`EXPERIMENTAL`의 기본값은 `True`다.** 새 collection이나 새로 고친 collection은 아직
    검증되지 않았다고 보수적으로 취급한다. `False`로 바꾸는 건 에이전트가 스스로 판단할 수
    없고, 그 collection을 맡은 **사용자가 명시적으로 승인**해야 한다
    ([/decisions/governance-and-review.md](../../../knowledge/decisions/governance-and-review.md)의
    "검증 기준은 에이전트가 제안, 사람이 승인" 원칙과 같다).
    - 승인 사실은 코드에 남긴다: `EXPERIMENTAL = False  # 사용자 승인: YYYY-MM-DD`.
    - 승인 기록이 없는 `EXPERIMENTAL = False`는 무효다 — 근거 없이 `True`로 되돌린다.
  - Collection에만 적용한다. 이 레포의 버전 차원은 collection 단위이고, item은 그 안에 속한
    데이터 묶음이라 독립된 버전 성숙도 개념이 없다.
  - `predecessor`/`successor`(새 버전 발행 시 옛 버전에 forward-pointer를 붙이는 것)는 정적
    상수가 아니라 "이전 버전을 참조"하는 실행 시점 로직이 필요해 이 규칙 밖이다. 미해결로
    남는다([/decisions/geovars-references-collection.md](../../../knowledge/decisions/geovars-references-collection.md) 참고).
- **날짜/시각 상수(`GENERATED_AT` 등)는 ISO 8601 문자열로 정의한다.** `datetime(...)` 생성자
  호출은 코드처럼 읽혀 상수 블록의 "데이터를 보고 파악한다"는 목표와 어긋난다. `datetime`
  객체가 필요한 자리에서 `datetime.fromisoformat(GENERATED_AT)`로 그때그때 변환한다.
- **`DESCRIPTION`이 모듈 docstring을 겸한다.** STAC에 발행되는 공개 설명과, 이 스크립트가 왜
  이렇게 짜였는지(예: 인프라 검증 겸용이라는 사실, 참고한 `knowledge/decisions/...` 경로)를
  하나의 문자열로 합친다.
  - [/decisions/knowledge-architecture.md](../../../knowledge/decisions/knowledge-architecture.md)의
    "데이터에 관한 맥락은 STAC에, 값과 근거는 같은 곳에" 원칙과 일치한다. 레포가 public이라
    `knowledge/decisions/...` 경로 언급도 외부에서 그대로 따라갈 수 있는 링크다.
  - 한국어로 쓴다(`description`의 기존 관행).
  - 여는 `"""` 바로 뒤에 내용을 붙이지 않고 줄바꿈한다(`"""\n내용...\n"""` 형태). 첫 줄부터
    내용이 시작되면 여는 따옴표와 텍스트가 붙어 읽기 불편하다.
- **`ASSET_KEY`는 기본적으로 완성된 값**(f-string)이다. item을 여러 개 만드는 collection처럼
  파일명 부분만 갈아끼워야 하면, `ASSET_KEY_TEMPLATE = "{collection_id}/version={version}/{filename}"`
  같은 템플릿을 두고 각 item 처리 단계에서 `.format(...)`으로 채우는 패턴을 권장한다(강제 아님
  — item이 하나뿐인 collection에 템플릿화는 과하다).

## Google-style docstring

**이 디렉터리(`pipeline/process/*.py`)에만 적용한다.** `geovars/` 패키지는 별도 컴포넌트이고
지금의 한국어 산문(WHY 중심) 스타일을 유지한다 — 소비층이 다르다(라이브러리 vs 사람이 직접
열어보는 처리 스크립트).

- `Processor` 클래스와 각 메서드, 그리고 모듈 헬퍼 함수에 Google-style docstring을 쓴다.
- 각 단계 메서드는 `Sets:` 섹션으로 어떤 `self.` 속성을 채우는지 밝힌다(아래 예시 참고).

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

    def build_item(self) -> None:
        """STAC Item을 구성하고 asset을 attach한다(아직 업로드 전).

        Sets:
            self.item: 구성된 pystac.Item.
        """
        ...

    def upload_asset(self) -> None:
        """geovars.pipeline.publish_asset()으로 asset을 업로드하고 checksum을 기록한다.

        Sets:
            self.checksum: 업로드된 파일의 Multihash(sha2-256).
        """
        ...

    def evaluate_asset(self) -> None:
        """업로드한 asset을 재검증한다. 실패하면 예외를 던진다."""
        ...

    def build_collection(self) -> None:
        """STAC Collection을 구성한다.

        Sets:
            self.collection: 구성된 pystac.Collection.
        """
        ...

    def register(self) -> None:
        """collection에 item을 붙이고 카탈로그에 등록한다."""
        ...

    @property
    def references(self) -> list[dict]:
        """하드코딩 데이터. 단계 메서드보다 아래, 클래스 제일 아래에 둔다."""
        return [...]


if __name__ == "__main__":
    Processor().run()
```

- **`run()`이 메서드 정의 중 최상단이다.** 나머지는 `run()`이 호출하는 순서대로 아래에 둔다.
- **`run()` 본문은 조건·반복 없이 `self.xxx()` 호출만 순서대로 나열한다.** 이름만 보고 무엇을
  하는지 알아야 한다("메서드 체이닝처럼 읽히게"라는 목표이지, 실제로 `self`를 반환해
  `.`으로 이어붙이라는 뜻은 아니다 — 그러면 상태를 반환값 없이 쌓는다는 원칙과 충돌한다).
- **단계 메서드는 결과를 인스턴스 속성에 저장하고, 다음 단계가 그 속성을 읽는다.** 반환값을
  `run()`이 지역 변수로 이어받아 다음 메서드 인자로 넘기지 않는다 — 그러면 `run()` 안에
  변수 스레딩이 생겨 "이름만 보고 흐름 파악"이 깨진다.
- **메서드 이름은 collection마다 자유롭다.** 고정된 이름의 인터페이스를 강제하지 않는다.
  item을 하나만 만드는 collection과 여러 개 만드는 collection은 처리 단계 자체가 다르므로,
  이름만 자기서술적이면 충분하다.
- `self` 상태를 전혀 안 쓰는 순수 로직(예: 한 행을 인용 문자열로 바꾸는 변환)은 인스턴스
  메서드로 두지 않는다. 아래 "순수 헬퍼 함수"를 본다.

### `evaluate_asset()` — 업로드 재검증

CI가 없으므로, 업로드가 실제로 성공했고 로컬 캐시가 read-through로 동작하는지 스크립트 스스로
확인한다.

```python
def evaluate_asset(self) -> None:
    path = s3_path(ASSET_KEY)
    cache_file = Path(path.fspath)
    mtime_before = cache_file.stat().st_mtime if cache_file.exists() else None

    data = path.read_bytes()
    if multihash_sha256(data) != self.checksum:
        raise ValueError(f"재다운로드한 asset의 checksum이 기록값과 다릅니다: key={ASSET_KEY}")

    mtime_after = cache_file.stat().st_mtime
    if mtime_before != mtime_after:
        raise ValueError(f"asset을 로컬 캐시 대신 재다운로드했습니다: key={ASSET_KEY}")
```

- **재읽기+checksum 일치**: `s3_path(...)`로 다시 읽은 바이트의 Multihash가 업로드 때 기록한
  `self.checksum`과 같은지 확인한다 — asset이 실제로 읽을 수 있는 상태인지 증명한다.
  세부는 [/decisions/cloudpathlib-cache-pattern.md](../../../knowledge/decisions/cloudpathlib-cache-pattern.md).
- **캐시 히트 확인**: 읽기 전후로 로컬 캐시 파일의 mtime이 그대로인지 본다. 바뀌었으면
  재다운로드가 일어난 것이라 `.cache/s3/`가 read-through로 동작하지 않는다는 신호다.
- 둘 중 하나라도 실패하면 예외를 던져 실행 자체를 실패시킨다.

## 순수 헬퍼 함수

`self` 상태를 읽거나 쓰지 않는 로직(예: 한 데이터 행을 인용 문자열로 바꾸는 변환)은 클래스
메서드가 아니라 모듈 함수로 뺀다. 위치는 **`Processor` 클래스 아래, `if __name__ ==
"__main__":` 위**다.

```python
def citation(ref: dict) -> str:
    """서지 데이터 한 행을 인용 문자열로 바꾼다."""
    ...
```

Python은 모듈 함수의 정의 순서를 신경 쓰지 않는다 — `run()`이 실제로 호출되는 시점(스크립트
맨 아래 `Processor().run()`)엔 이미 모듈 전체가 로드돼 있으므로, 헬퍼가 클래스보다 아래 있어도
동작에 영향이 없다. 읽는 사람은 어차피 클래스(핵심 흐름)를 먼저 보고, 필요할 때만 아래로
내려가 헬퍼를 확인한다.

## S3(R2) 업로드/다운로드

- 다운로드: `geovars.pipeline.s3_path(key) -> S3Path`를 그대로 써서 `.open()`/`.read_bytes()`/
  `.download_to()`를 호출한다. 별도 캐시 판단 로직을 만들지 않는다 — cloudpathlib이 로컬/
  클라우드 mtime 비교로 알아서 한다.
- 업로드: `geovars.pipeline.publish_asset(asset, key, write)`. 호출 순서가 고정되어 있다.
  1. `pystac.Asset(...)` 생성.
  2. `item.add_asset("<name>", asset)`로 owner를 먼저 확보한다.
     - 이 순서를 어기면 `FileExtension.ext(asset, add_if_missing=True)`가
       `pystac.STACError`를 낸다.
  3. `publish_asset(asset, key, write=lambda f: ...)`를 호출한다.
  - 이 함수를 감싸는 Processor 단계 메서드는 `publish_asset`이 아니라 `upload_asset`처럼
    다른 이름을 쓴다 — 임포트한 함수 이름과 겹치면 "업로드(스토리지 계층)"와 "게시(STAC
    카탈로그 계층)"가 헷갈린다.

## STAC 등록

- extension은 항상 pystac 공식 accessor로 적용한다: `XxxExtension.ext(obj,
  add_if_missing=True).필드 = ...`. 원본 dict/JSON을 직접 조작하지 않는다.
- `VersionExtension.ext(collection, add_if_missing=True)`에 `version`/`experimental`/
  `deprecated`를 위 모듈 상수 그대로 대입한다.
- 카탈로그 등록은 `geovars.catalog.register_collection(self.collection, VERSION)`로 한다.
  커스텀 `normalize_and_save` 호출을 다시 짜지 않는다.
  - `catalog_root` 인자는 기본값이 cwd 기준 상대경로 `"stac-metadata"`라 생략해도 된다.
    `pipeline/run.py`가 Docker 컨테이너의 cwd를 항상 레포 루트로 고정하기 때문이다(`-w
    /workspace`). `pipeline/run.py`를 거치지 않고 다른 위치에서 직접 실행할 때만 명시적으로
    넘긴다.

## 스크립트 간 재사용 금지

`pipeline/process/*.py`끼리는 서로 import하거나 코드를 공유하지 않는다. 각 스크립트는
`geovars` 패키지 pin 외에는 완전히 독립적이다.

- 처리 스크립트는 의도적으로 자기완결·비-DRY다 — 옛 스크립트가 새 스크립트의 변경으로
  재현성이 깨지면 안 되기 때문이다
  ([/decisions/pipeline-architecture.md](../../../knowledge/decisions/pipeline-architecture.md)).
- Ponytail 하네스의 "이미 있는 코드는 재사용하라" 규칙은 **같은 스크립트 안**이나 `geovars`
  패키지 유틸에는 그대로 적용되지만, **다른 `pipeline/process/<id>.py`의 코드를 가져오는
  것에는 적용하지 않는다.**
- 여러 스크립트에서 비슷한 로직이 반복되는 게 아깝게 느껴져도, 공유가 필요하면 `geovars`
  패키지의 공용 유틸(`geovars.pipeline` 등)로 올리고 git-commit pin으로 소비한다. 스크립트끼리
  직접 참조하지 않는다.

## 검증

- CI가 없으므로 검증은 실제로 스크립트를 돌려서 한다.
  - `python pipeline/run.py <collection-id> [--relock]`로 실행한다.
  - 재실행 결과를 `git diff --stat stac-metadata/`로 확인한다. 입력이 그대로면 diff가 없어야
    한다.
  - 새 S3 코드 경로를 건드렸다면 실제 R2에 대고 최소 한 번은 돌려, 업로드와 checksum
    메타데이터가 실제로 반영되는지 확인한다. `evaluate_asset()`이 매 실행마다 이 확인의
    상당 부분을 자동으로 한다.
- `--relock`은 의존성을 의도적으로 바꿀 때만 쓴다. lock이 바뀌면 커밋이 필수다.
- 데이터 본문(`@property`로 둔 하드코딩 데이터 등)을 고쳤다면 `VERSION`을 올린다. `ASSET_KEY`가
  `f"...version={VERSION}/..."` 패턴이라 자동으로 새 key가 된다. 근거:
  [/decisions/versioning-and-corrections.md](../../../knowledge/decisions/versioning-and-corrections.md).
- 스크립트를 고치면 `uvx ruff format <path>`와 `uvx ruff check --fix <path>`를 돌린다.
  설정은 레포 루트 `ruff.toml`. 버전은 pin하지 않는다 — 재현성 3층 pin의 대상이 아니라
  커밋 전 스타일 정리 도구일 뿐이다.

## 마칠 때

- 스크립트를 다 쓴 뒤, 처음부터 끝까지 다시 읽으며 이 스킬의 규칙과 하나씩 대조한다(상수
  배치·순서, `run()`이 조건·반복 없이 호출만 나열하는지, `EXPERIMENTAL` 승인 여부,
  `evaluate_asset()` 존재 여부 등). 방금 쓴 사람이 아니라 처음 보는 사람 입장에서 읽는다.
- `capture-knowledge`로 이번 작업에서 생긴 새 결정·주의사항을 남긴다.
- `geovars` 쪽 코드를 고쳤다면, 커밋 후 PEP723 헤더의 pin 커밋 해시를 그 커밋으로 갱신하고
  `--relock`한다.
