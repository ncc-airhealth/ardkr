# stac-metadata

STAC 카탈로그를 **JSON으로 직접 커밋**한다 (데이터에 관한 사실의 SSOT).
표준 STAC 도구(stac-browser 등)가 URL만으로 크롤할 수 있게 한다.

- **버전 차원이 여기 산다.** 루트 카탈로그에는 collection당 **최신 버전만** child로 노출하고, 과거 버전 메타데이터도 전부 보관해 버전으로 resolve 가능하게 한다.
- asset `href`에는 **R2 객체 key**를 그대로 저장한다(self-describing).
- 데이터 해석을 바꾸는 정정은 새 버전으로. 옛 버전에는 `deprecated`+`successor-version`을 부착한다.

세부: [`../.agents/skills/pipeline-publish-verify/SKILL.md`](../.agents/skills/pipeline-publish-verify/SKILL.md)

## root catalog.json

`catalog.json`은 collection이 아직 없는 빈 root STAC Catalog다(pystac `normalize_and_save(catalog_type=SELF_CONTAINED)`로 생성, 상대경로만 사용 — 서빙 URL이 확정되면 `ABSOLUTE_PUBLISHED`로 전환 검토).
Collection을 추가할 때는 다음 load-mutate-save 절차를 따른다(카탈로그와 개별 collection 파일이 어긋나지 않게 pystac으로만 조작):

```python
import pystac

catalog = pystac.Catalog.from_file("stac-metadata/catalog.json")
catalog.add_child(collection)  # collection 객체 생성/수정
catalog.normalize_and_save("stac-metadata", catalog_type=pystac.CatalogType.SELF_CONTAINED)
```
