---
name: write-pipeline-script
description: 파이프라인 처리 스크립트(`pipeline/process/*.py`)를 새로 쓰거나 고칠 때 따르는 규약. 지금은 재사용·재현성 규칙만 담고, 전체 작성 워크플로우는 추후 완성 예정.
---

# write-pipeline-script

파이프라인 처리 스크립트(`pipeline/process/*.py`)를 쓸 때 따르는 규약.
일반 파이썬 규칙은 `../write-python/SKILL.md`를 따르고, 여기서는 파이프라인 전용 규칙만 더한다.

## 재사용과 재현성

스크립트는 완전히 재현 가능해야 한다.

- `pipeline/process/*.py`끼리 import·코드 공유 금지
- 의존성은 lock과 commit-pin으로 고정
- 공용 로직이 필요하면 `ardkr` 패키지로 올려 commit-pin으로 활용

## PySTAC

처리 스크립트에서 PySTAC 객체·extension을 생성하거나 수정할 때는 `../use-pystac/SKILL.md`를 따른다.

## 추후 작성

이 skill은 파이프라인 스크립트 작성 워크플로우를 엮는 형태로 완성 예정이다.
지금은 위 규칙만 담겨 있다.
