# pipeline/images

시스템 환경 정의를 **날짜 버전별**로 둔다: `images/<YYYY.MM.DD>/`에
`pixi.toml` + `pixi.lock` + `Dockerfile`.

- **Docker**가 OS 층을, **pixi**가 GDAL/GEOS/PROJ/uv(conda-forge)를 고정한다.
- 정규 arch는 `linux/amd64`.
- 빌드된 이미지는 레지스트리에 **보존**한다(냉동). 여기 커밋되는 것은 **빌드 정의**이지
  이미지 blob이 아니다.
- 처리 스크립트가 상단 `[tool.geovars] image`로 이 중 하나를 가리킨다. 시스템 deps를
  올리면 새 날짜 디렉토리를 만들고, 옛 스크립트는 옛 버전을 계속 가리킨다.

세부: [`../../knowledge/decisions/pipeline-architecture.md`](../../knowledge/decisions/pipeline-architecture.md)
