"""knowledge/ OKF frontmatter 조회.

문서 목록을 손으로 쓴 index.md 대신 이 스크립트로 조회한다.
frontmatter 문법은 일반 YAML이 아니라 이 레포가 정한 제약된 형태다.

  - 모든 필드는 한 줄짜리 `key: value`다.
  - 유일한 리스트 필드는 `tags`이며 `[a, b, c]` 형태로만 쓴다.

의존성 없이 시스템 python3로 바로 실행한다. 한 줄에 문서 하나씩 JSON을 찍는다(JSONL).

  python3 .claude/skills/recall-knowledge/list_knowledge.py knowledge/decisions --type decision
  python3 .claude/skills/recall-knowledge/list_knowledge.py knowledge/ --tag stac
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    if "---" not in lines[1:]:
        return None
    end = lines[1:].index("---") + 1
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def parse_tags(raw: str) -> list[str]:
    raw = raw.strip().removeprefix("[").removesuffix("]")
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path, help="예: knowledge/ 또는 knowledge/decisions")
    parser.add_argument("--type", dest="type_", help="frontmatter type으로 필터")
    parser.add_argument("--tag", help="tags에 포함된 태그로 필터")
    args = parser.parse_args()

    for path in sorted(args.root.rglob("*.md")):
        fields = parse_frontmatter(path.read_text(encoding="utf-8"))
        if fields is None or "type" not in fields:
            continue
        if args.type_ and fields.get("type") != args.type_:
            continue
        tags = parse_tags(fields.get("tags", "[]"))
        if args.tag and args.tag not in tags:
            continue
        record = {
            "path": str(path),
            "type": fields.get("type", ""),
            "title": fields.get("title", ""),
            "description": fields.get("description", ""),
            "tags": tags,
            "timestamp": fields.get("timestamp", ""),
        }
        print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    main()
