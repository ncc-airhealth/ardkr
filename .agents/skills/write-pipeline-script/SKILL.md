---
name: write-pipeline-script
description: 파이프라인 처리 스크립트(`pipeline/process/*.py`)를 새로 쓰거나 고칠 때 따르는 규약. 스크립트 구조·stage 함수·verify stage·재현성 규칙을 담는다.
---

# write-pipeline-script

파이프라인 처리 스크립트(`pipeline/process/*.py`)를 쓸 때 따르는 규약.
스크립트 하나가 collection 하나를 만든다.

일반 파이썬 규칙은 `../write-python/SKILL.md`, PySTAC 사용법은 `../use-pystac/SKILL.md`를 따른다.
승인이 필요한 행위는 `../repo-rule/SKILL.md`가 정한다.
메타데이터 내용·`__doc__` 작성은 `../design-stac-metadata/SKILL.md`를 따른다.
여기서는 파이프라인 전용 규칙만 더한다.

## 용어

- **stage 함수** — `main`이 인자 없이 호출하는 처리 단위. 스크립트의 뼈대
- **util 함수** — stage 함수가 쓰는 헬퍼. `_` prefix, 인자 허용
- **verify stage** — 마지막 stage 함수. 결과가 맞는지 판정함

## 파일과 식별자

- 파일명은 collection id와 같게 지음 (`arcgis-mdl-dmz.py` ↔ `id="arcgis-mdl-dmz"`)
- 한 스크립트에 collection 하나만 정의함
- 의존성 lock(`*.py.lock`)은 스크립트와 함께 갱신·커밋함
- 의존성을 고치면 `python3 pipeline/run.py <collection-id> --relock`으로 lock을 다시 만듦. 안 하면 `--frozen` 실행이 실패함

## 작성 순서

스크립트 상단부터 아래 순서로 쓴다.

1. PEP 723 의존성 정의 (`# /// script`)
2. `__doc__`
3. import
4. 환경변수 로딩·상수 정의
5. collection 객체 정의
6. `main`
7. stage 함수 (마지막은 verify stage)
8. util 함수
9. `if __name__ == "__main__":` 실행 코드

4~9 각 블록 앞에 구분선 주석을 둔다.
이름은 `상수`·`collection`·`main`·`stage`·`util`·`실행`이다.
예: `# 실행 ------------------------------------------------------------------------`

상수는 주석으로 두 묶음으로 나눈다.

- 사람이 실행마다 조정하는 값 (`VERSION`, `EXPERIMENTAL` 등)
- 고정 상수 (출처 URL, 원본 EPSG, 기준 시각, 경로 등)

`datetime.now()`처럼 실행마다 바뀌는 값은 그 값이 무슨 시각인지 이름으로 밝힌다.
관측 시각을 모른다고 처리 시각으로 대신 채우지 않는다.
취득 시각을 시간 범위에 쓴다면 그 해석은 `../design-stac-metadata/SKILL.md`에 따른다.

## main과 stage 함수

- `main` 본문에는 stage 함수 호출만 둠. 조건·반복·계산 금지
- stage 함수는 이름만으로 무슨 일을 하는지 알 수 있어야 함. 동사구로 지음 (`define_item_assets`, `build_item_from_source`, `register_collection`, `verify_registration`)
- stage 함수는 인자를 받지 않음. 입력은 상수와 모듈 전역 collection에서 읽음
- 인자가 필요한 로직은 util 함수로 내림
- stage 간 상태는 collection 객체로만 넘김. stage끼리 주고받을 임시 전역 변수를 만들지 않음

원격이나 카탈로그를 바꾸는 일은 stage를 나눈다.

- STAC 등록과 원격 업로드는 각각 별도 stage로 둔다.
- 원본을 받아 가공하고 로컬 캐시에 쓰는 일은 한 stage에 넣어도 된다.

## verify stage

verify stage는 마지막 stage 함수로 반드시 둔다.

**기계적 판정** — 실패하면 예외로 멈춤. 경고만 찍고 넘어가거나 부분 성공으로 등록하지 않음.

- 저장된 파일을 다시 읽어 검증함. 메모리 객체는 link href가 비어 스키마 검증을 통과하지 못함
- STAC 스키마 검증 (`pystac[validation]`의 `validate()`)
- asset 실제 판독. 파일을 다시 열어 checksum·size가 STAC에 적은 값과 같은지 확인
- 데이터 불변식. 행 수, 좌표계, 범위가 STAC에 적은 값과 어긋나지 않는지 확인

**사람 판정** — 해석이 필요한 항목은 자동으로 통과시키지 않음.

- 판정할 항목과 근거를 표준출력에 보고함
- `input()`으로 대기하지 않음
- 사람이 출력을 읽고 판정한 결과는 상수(`EXPERIMENTAL` 등)나 메타데이터에 남김

## 재사용과 재현성

스크립트는 완전히 재현 가능해야 한다.

- `pipeline/process/*.py`끼리 import·코드 공유 금지
- 의존성은 lock과 commit-pin으로 고정
- 공용 로직이 필요하면 `ardkr` 패키지로 올려 commit-pin으로 활용

## 참고 구현

`pipeline/process/arcgis-mdl-dmz.py`가 이 규격의 참고 구현이다.
