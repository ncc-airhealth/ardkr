---
name: use-pystac
description: PySTAC 객체·extension을 생성하거나 수정할 때 발동. built-in extension은 .ext accessor를 우선 쓰고, 잠긴 버전의 공식 문서와 직렬화 결과를 확인한다.
---

# use-pystac

PySTAC으로 STAC 객체와 extension을 다룰 때 따르는 규약.
검증된 최소 사용법만 담는다.

## 버전과 문서

- 실행 환경에 **잠긴 PySTAC 버전**을 먼저 확인함 (스크립트 PEP 723 lock, 패키지 고정 버전 등)
- 그 버전의 공식 문서를 기준으로 삼음
- extension accessor API: [pystac.extensions.ext](https://pystac.readthedocs.io/en/latest/api/extensions/ext.html)

## built-in extension

built-in extension은 `.ext` accessor를 우선 쓴다.

- 새 객체: `obj.ext.add("<name>")` 후 필드 설정
- 존재 여부가 불확실한 기존 객체: `obj.ext.has("<name>")`로 확인. 필요하면 `add()`
- 관련 필드는 개별 대입보다 `apply(...)`로 함께 설정

예시 (식별자 이름·인자는 해당 extension 문서를 따름):

```python
item.ext.add("sci")
item.ext.sci.apply(publications=[...])

collection.ext.add("version")
collection.ext.version.apply(version="1.0.0", experimental=True, deprecated=False)
```

## 값 객체와 예외

- `Publication` 같은 값 객체는 해당 extension 모듈에서 import
- accessor 미지원이거나 classmethod가 더 명확할 때만 `*Extension.ext(...)` 허용

## 직렬화 확인

- extension URI와 필드가 기대와 같은지 `to_dict()`로 확인
- 동작·직렬화가 애매하면 같은 입력으로 classmethod 방식과 accessor 방식의 `to_dict()`를 비교
