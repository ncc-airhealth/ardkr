---
name: manual-pipeline
description: pipeline/process/**.py 스크립트 또는 그 실행·환경·catalog 연계를 다룰 때 활성화.
---

# manual-pipeline

`pipeline/process/**.py` 스크립트를 통한 데이터·메타데이터 구현과 실행 워크플로우를 정의한다.

# 작업 순서


## 1. 탐색적 조사

`./reference/analysis-ready-data.md`에 따라 사용자가 제시한 데이터에 대해 **조사 및 검토**

## 2. 스크립트 뼈대 생성

`./reference/pipeline-script-example.py`를 `pipeline/process/<collection-id>.py`로 복사

## 3. 파이프라인 스크립트 개선

`pipeline/process/<collection-id>.py`를 개선

  3-1. 조사로 확인한 정보를 `COLLECTION_STAC_CONTENT`에 반영
  3-2. `PipelineCollection.process()` 구현
  3-3. `PipelineCollection.verify_auto()` 구현
  3-4. `PipelineCollection.checklist` 작성
  3-5. 의존성을 바꿨으면 script lock을 갱신하고 확인

## 4. checklist 검토 (사용자 개입 필수)

사용자(인간)가 직접 `PipelineCollection.checklist`를 확인하고, 확인한 항목을 True로 변경한다.

## 5. 검토용 실행

`experimental=True` 상태로 pipeline script를 실행한다. 
(`Publish blocked: \`experimental=False\`` 오류가 발생하면 성공이다.)

## 6. 생성 결과 점검 및 개선

  6-1. 생성된 metadata를 검토 (`./reference/stac-metadata-checklist.md`에 따라 진행)
  6-2. `pipeline/process/<collection-id>.py`를 검토 (`./reference/pipeline-script-checklist.md`에 따라 진행)
  6-3. 생성된 `catalog/<collection-id>/<version>/**.json`과 `pipeline/process/<collection-id>.py`를 검토 (`./reference/analysis-ready-data.md`에 따라 진행)
  6-4. 검토 결과 문제 없으면 (7.)으로 이동
  6-5. 검토 결과 개선 필요하면 (6-1), (6-2), (6-3)에서 검토한 내용을 기반으로 (## 3.)부터의 과정을 반복

## 7. 최종 검토 (사용자 개입 필수)

사용자(인간)가 최종 결과를 확인하고 배포를 승인한다. 

## 8. 최종 실행과 GitHub 반영

8-1. 배포 승인을 받은 뒤 `experimental=False`로 pipeline을 다시 실행한다.
8-2. 최종 실행 결과와 asset publish 결과를 확인한다.
8-3. 별도의 사용자 승인을 받은 뒤 GitHub `main` 브랜치에 push한다.
