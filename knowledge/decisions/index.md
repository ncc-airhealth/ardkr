# Decisions

grilling 세션(2026-07-20)에서 확정한 설계 결정 기록. 각 문서는 결정 / 근거 /
기각한 대안 / 미해결을 담는다.

- [/decisions/knowledge-architecture.md](/decisions/knowledge-architecture.md) —
  STAC(데이터 사실) vs OKF(간접 지식) 경계, 우선순위 규칙, provenance 위치, description
  한국어·caveat 3칸 권장 템플릿
- [/decisions/versioning-and-corrections.md](/decisions/versioning-and-corrections.md) —
  해석-규정 필드 불변, 정정=새 버전(MAJOR.MINOR.PATCH 고정), deprecated/successor
  forward-pointer
- [/decisions/reproducibility.md](/decisions/reproducibility.md) —
  처리 재현성, 3층 pin, 원본·코드북 박제, lock 필수(CI 없이 정책으로만 강제), 삭제금지·냉동
- [/decisions/catalog-and-access.md](/decisions/catalog-and-access.md) —
  static STAC JSON, 최신-only 카탈로그 / 전-버전 레포, 사용자·접근, 자격증명 게이트
- [/decisions/pipeline-architecture.md](/decisions/pipeline-architecture.md) —
  모노레포 구조, 자기완결 처리 스크립트(PEP723+lock), Docker+pixi 환경, Python 래퍼, geovars 패키지
- [/decisions/governance-and-review.md](/decisions/governance-and-review.md) —
  self-review 수용, 사용자 피드백 루프, 처리 절차, 검증기준·오라클
- [/decisions/knowledge-capture.md](/decisions/knowledge-capture.md) —
  continuous 포착 2층(워크플로/상시 지침) — CI 미도입 결정으로 PR 냄새 게이트 제거
- [/decisions/infrastructure.md](/decisions/infrastructure.md) —
  팀 소유 R2 버킷, 자격증명·세부설정만 암묵지 예외 / 버킷명·엔드포인트 등 비-비밀 포인터는
  레포에 기록
