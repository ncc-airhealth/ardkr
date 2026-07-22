"""list_knowledge.py의 frontmatter 파싱 로직에 대한 최소 self-check.

python3 .claude/skills/recall-knowledge/test_list_knowledge.py 로 실행한다.
"""

from list_knowledge import parse_frontmatter, parse_tags


def test_parse_frontmatter() -> None:
    text = "---\ntype: decision\ntitle: 제목\ntags: [a, b, c]\n---\n\n# 본문\n"
    fields = parse_frontmatter(text)
    assert fields == {"type": "decision", "title": "제목", "tags": "[a, b, c]"}


def test_parse_frontmatter_no_dashes() -> None:
    assert parse_frontmatter("# 제목만 있음\n") is None


def test_parse_tags() -> None:
    assert parse_tags("[stac, versioning, corrections]") == ["stac", "versioning", "corrections"]
    assert parse_tags("[]") == []


if __name__ == "__main__":
    test_parse_frontmatter()
    test_parse_frontmatter_no_dashes()
    test_parse_tags()
    print("ok")
