# stac-metadata

STAC 카탈로그를 **JSON으로 직접 커밋**한다 (데이터에 관한 사실의 SSOT). 표준 STAC
도구(stac-browser 등)가 URL만으로 크롤할 수 있게 한다.

- **버전 차원이 여기 산다.** 루트 카탈로그에는 collection당 **최신 버전만** child로 노출하고,
  과거 버전 메타데이터도 전부 보관해 버전으로 resolve 가능하게 한다.
- asset `href`에는 **R2 객체 key**를 그대로 저장한다(self-describing).
- 데이터 해석을 바꾸는 정정은 새 버전으로. 옛 버전에는 `deprecated`+`successor-version`을
  부착한다.

세부: [`../knowledge/decisions/catalog-and-access.md`](../knowledge/decisions/catalog-and-access.md),
[`../knowledge/decisions/versioning-and-corrections.md`](../knowledge/decisions/versioning-and-corrections.md)
