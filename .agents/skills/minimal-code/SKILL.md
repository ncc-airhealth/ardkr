---
name: minimal-code
description: Use before writing or reviewing any code in this repo — a ladder of checks (need it at all? already exists? stdlib? native? existing dependency? one line?) to avoid over-engineering.
---

# minimal-code

코드를 쓰기 전에 아래 사다리를 위에서부터 확인한다. 먼저 걸리는 단만 쓰고 멈춘다.

1. **꼭 필요한가?** 추측성 필요면 만들지 않는다.
2. **레포에 이미 있는가?** 같은 스크립트 안이나 `geovars` 패키지 유틸 — 있으면 재사용한다. 예외: `pipeline/process/*.py` 스크립트끼리는 이 규칙을 적용하지 않는다 — 이유는 [pipeline-script-shape](../pipeline-script-shape/SKILL.md)의 "스크립트 간 재사용 금지".
3. 표준 라이브러리로 되는가? 그걸 쓴다.
4. 플랫폼/도구 네이티브 기능으로 되는가? 그걸 쓴다.
5. 이미 설치된 의존성으로 되는가? 그걸 쓴다. 새 의존성을 위해 몇 줄짜리 코드를 대체하지 않는다.
6. 한 줄로 되는가? 한 줄로 쓴다.
7. 그래도 안 되면 그때 최소한의 코드를 쓴다.

## 규칙

- 요청받지 않은 추상화를 만들지 않는다(구현체 하나짜리 인터페이스, 값이 안 바뀌는 설정 등).
- "나중을 위한" 보일러플레이트를 두지 않는다.
- 삭제가 추가보다 우선한다. 지루한 코드가 똑똑한 코드보다 낫다.
- 의도적으로 잘라낸 corner(전역 락, O(n²) 스캔 등)는 `# ponytail:` 주석으로 한계와 업그레이드 조건을 남긴다.

## 예외 (절대 생략하지 않음)

트러스트 바운더리의 입력 검증, 데이터 손실을 막는 에러 처리, 보안, 명시적으로 요청된 것은 절대 단순화하지 않는다.
