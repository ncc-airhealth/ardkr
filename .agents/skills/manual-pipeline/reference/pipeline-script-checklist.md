# pipeline script checklist

`pipeline/process/<collection-id>.py`

## 실행 환경

`pipeline/run.py`로 실행한다. (의존성 갱신이 필요한 경우, `--relock`을 적용)

- [ ] 파일명과 collection의 id가 일치한다.
- [ ] PEP 723 의존성과 `[tool.ardkr] image`가 선언되어 있다.
- [ ] 레포 루트에서 `pipeline/run.py`로 실행된다.
- [ ] 로컬 경로·대화형 입력·하드코딩한 인증정보에 의존하지 않는다.

## 재현성

- [ ] 결과 재현에 필요한 입력·코드·실행 환경을 확인할 수 있다.
- [ ] 실행 시각·난수·입력 상태의 영향을 고정하거나 기록한다.

## 가독성

- [ ] Helper 메서드('_' prefix 적용)를 활용한다.
- [ ] `pipeline/ruff.toml`을 적용한다.

## STAC 메타데이터 처리

- [ ] Collection/Item의 Asset 정의 및 생성 시 `.pipe.define_asset()`를 사용한다.
- [ ] Asset 파일의 로컬 캐시 경로 지정 시 `asset.pipe.path()`를 사용한다.
- [ ] Asset 파일의 file metadata 계산 시 `asset.pipe.apply_digest()`를 사용한다.
- [ ] `COLLECTION_STAC_CONTENT`에 placeholder·예시 기본값·임시 범위가 남아 있지 않다.

## `.process()` 메서드

- [ ] 세부 로직은 Helper 메서드를 활용한다.
- [ ] 입력 데이터를 읽고 가공해 필요한 item·asset을 생성한다.
- [ ] 미완성 처리·검증 코드가 남아 있지 않다.
- [ ] item·asset 생성 및 asset 파일명 규칙이 코드에 드러나 있다.
- [ ] 파일을 생성한 모든 asset에 digest를 적용한다.
- [ ] 처리할 수 없는 입력이나 오류를 조용히 건너뛰지 않는다.

## `verify_auto()`

- [ ] 세부 로직은 Helper 메서드를 활용한다.
- [ ] 자동 검증에 실패하면 script 실행이 실패한다.
- [ ] 입력·asset·metadata를 수정하지 않는다.

## 인간 검토

- [ ] 사용자가 checklist의 질문이 collection에 맞는지 확인했다.
- [ ] 사용자가 각 항목을 생성 결과와 대조해 확인했다.
- [ ] 사용자가 확인한 항목만 `True`이고, 미확인 항목은 `False`다.
- [ ] 사용자가 생성된 catalog와 asset을 직접 열어 확인했다.
