# CLAUDE.md

이 레포는 agent-native다 — 모든 작업은 에이전트와의 대화로 하고, 모든 지식은
레포 안에 둔다. 세부·근거는 knowledge/에 있다.

## 지식 위치
- 데이터에 관한 사실 → STAC (Collection/Item JSON)
- 그 외 지식(결정·기관 문의 이력·처리법·주의사항) → knowledge/ (OKF)

## 상시 행동
- 작업 시작 전: `recall-knowledge`로 관련 과거 결정·연락·주의사항 조회.
- 작업 마치기 전: 새 지식이 생겼으면 `capture-knowledge`로 반영(완료 조건).

## 절대 규칙 (되돌릴 수 없음)
- 데이터·메타데이터 삭제 금지 (deprecated는 냉동).
- 데이터 해석을 바꾸는 정정은 in-place 금지, 새 version으로 발행.

세부 결정·처리 절차·그 외 규칙 → knowledge/decisions/index.md
