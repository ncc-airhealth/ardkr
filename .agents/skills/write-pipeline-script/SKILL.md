---
name: write-pipeline-script
description: 파이프라인 처리 스크립트(`pipeline/process/*.py`)를 새로 쓰거나 고칠 때 발동.
---

# write-pipeline-script

파이프라인 처리 스크립트(`pipeline/process/*.py`)를 쓸 때 따르는 규약.
스크립트 하나가 collection 하나를 만든다.

- 일반 파이썬 규칙은 `../write-python/SKILL.md`를 따름
- PySTAC 사용법은 `../use-pystac/SKILL.md`를 따름
- STAC 내용의 구성은 `../design-stac-metadata/SKILL.md`를 따름

## 작업 순서

1. 스크립트 뼈대를 생성 (`## 스크립트 구성` 참조)
2. `../inspect-data-quality/SKILL.md`로 원본·출처를 조사하며 재귀적으로 개선
3. 이 skill 규칙 전체를 최종 검토

## 파일과 식별자

- 파일명은 collection id와 동일 (`esri-mdl-dmz.py` ↔ `id="esri-mdl-dmz"`)
- 한 스크립트에 collection 하나만 정의
- 빌더 클래스명은 `PipelineCollection`
- 의존성 lock(`*.py.lock`)은 스크립트와 함께 갱신

## 스크립트 구성

상단부터 아래 순서.

1. PEP 723 의존성 (`# /// script`) — `ardkr[pipeline]` 포함
2. `__doc__`
3. import
4. 환경변수 로딩·상수
5. collection STAC dict
6. `PipelineCollection` 클래스
7. `if __name__ == "__main__": PipelineCollection.build()`


## PipelineCollection 계약

`ardkr.pipeline.CollectionBuilder`를 상속한다.

- `collection`, `manual_checklist`는 **클래스 속성**으로 둔다
- 구현 메서드: `process`, `verify_auto`
- 생명주기는 `build()`가 고정: `process → verify_auto → verify_manual → publish`
- asset 접근은 `self.collection.assets[...]`로 명시. 빌더에 assets 위임 없음
- href·경로는 accessor: `collection.kr.asset_href(...)`, `asset.kr.path`
- 스크립트끼리 import·코드 공유 금지. 공용 로직은 `ardkr` 패키지로

## 검증

- `verify_auto`: 실패 시 예외. 저장된 파일을 다시 읽어 좌표계·행 수 등 불변식 확인
- `manual_checklist`: `{질문: bool}`. **False는 사람 미확인** → build 중단. 사람이 True로 뒤집어 sign-off

## 발행

- `experimental=True`이면 publish는 수행되지 않는다 (프레임워크가 중단)
- 에이전트는 사용자 승인 없이 `experimental=False`로 바꾸지 않는다 (`../repo-rule/SKILL.md`)
- 발행·체크섬·로컬 미러 경로는 프레임워크 책임. 스크립트가 직접 업로드하지 않음

## 참고 구현

`pipeline/process/esri-mdl-dmz.py`
