#!/usr/bin/env python3
"""Validate local HTML assets, route destinations, and entry-page navigation."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str, str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for key in ("href", "src", "action"):
            if values.get(key) is not None:
                self.references.append((tag, key, str(values[key]), values))


def local_target(source: Path, value: str) -> Path | None:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or value.startswith(("data:", "blob:", "javascript:")):
        return None
    if not parsed.path:
        return source if parsed.fragment else None
    path = unquote(parsed.path)
    target = ROOT / path.lstrip("/") if path.startswith("/") else source.parent / path
    target = target.resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError as error:
        raise AssertionError(f"{source.relative_to(ROOT)} leaves repository: {value}") from error
    if target.is_dir() or path.endswith("/"):
        target /= "index.html"
    return target


html_files = sorted(path for path in ROOT.rglob("*.html") if ".git" not in path.parts)
assert html_files
missing: list[str] = []
invalid_placeholders: list[str] = []

for source in html_files:
    parser = ReferenceParser()
    parser.feed(source.read_text(encoding="utf-8"))
    for tag, key, value, attrs in parser.references:
        if value == "#" and not attrs.get("data-go"):
            invalid_placeholders.append(f"{source.relative_to(ROOT)}: {tag}[{key}]={value}")
        target = local_target(source, value)
        if target is not None and not target.exists():
            missing.append(f"{source.relative_to(ROOT)} -> {value} ({target})")

assert not missing, "missing local destinations:\n" + "\n".join(missing)
assert not invalid_placeholders, "unhandled placeholder links:\n" + "\n".join(invalid_placeholders)

entry_expectations = {
    "index.html": ("brand-intelligence/", "owner-yarns/", "daily/", "customer-sharing/", "status/"),
    "brand-intelligence/index.html": ("../", "../owner-yarns/", "../daily/", "../customer-sharing/", "../stylem/", "../status/"),
    "owner-yarns/index.html": ("../", "../brand-intelligence/", "../daily/", "../status/"),
    "daily/index.html": ("../", "../brand-intelligence/", "../customer-sharing/", "../status/"),
    "customer-sharing/index.html": ("../", "../brand-intelligence/", "../daily/", "../stylem/", "../status/"),
    "status/index.html": ("../", "../brand-intelligence/", "../owner-yarns/", "../daily/", "../customer-sharing/"),
}
for name, destinations in entry_expectations.items():
    text = (ROOT / name).read_text(encoding="utf-8")
    for destination in destinations:
        assert f'href="{destination}"' in text, f"{name} missing navigation to {destination}"

wrapper = (ROOT / "brand-intelligence/index.html").read_text(encoding="utf-8")
assert "./index-current.html" in wrapper
assert "./yarn-glossary.html" in wrapper
inbox = (ROOT / "brand-intelligence/index-current.html").read_text(encoding="utf-8")
assert 'src="./app.html?v=0.4.7"' in inbox

owner_yarns = (ROOT / "owner-yarns/index.html").read_text(encoding="utf-8")
assert "../data/yarn-catalog/mz100-catalog-2000.json" in owner_yarns
assert "kc_v04_handoff_queue_v1" in owner_yarns
for batch in (
    "2026-08-08-weijie-hesheng-batch1.json",
    "2026-08-08-weihai-yaxin-chengyun-batch2.json",
    "2026-08-10-mz100-yarn-research-batch3.json",
    "2026-08-12-twin-win-company-factory-batch4.json",
    "2026-08-12-rope-picnic-gdm56050-batch5.json",
):
    assert batch in owner_yarns
    assert (ROOT / "data/manual-intake" / batch).is_file()

print(f"navigation links: OK ({len(html_files)} HTML files; all local assets and registered entry destinations resolve)")
