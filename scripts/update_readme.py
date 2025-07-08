#!/usr/bin/env python3
"""Regenerate the README resource list.

The script scans subdirectories of the repository root for book folders
containing an ``index.html`` file. The ``<title>`` tag is used to obtain
human friendly titles. Lines between ``BEGIN`` and ``END`` markers in
``README.md`` are replaced with an alphabetically sorted list linking to
these books.
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"

BEGIN = "<!-- BEGIN AUTO-GENERATED RESOURCE LIST -->"
END = "<!-- END AUTO-GENERATED RESOURCE LIST -->"

def extract_title(html_path: pathlib.Path) -> str:
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
    if not m:
        return html_path.parent.name
    title = m.group(1).strip()
    # Remove trailing segments like "– Simple Book Publishing"
    title = re.split(r"\s+[\-\u2013]\s+", title)[0]
    return title

def gather_resources() -> list[tuple[str, str]]:
    resources = []
    for p in sorted(ROOT.iterdir()):
        if not p.is_dir():
            continue
        index_file = p / "index.html"
        if not index_file.is_file():
            continue
        title = extract_title(index_file)
        resources.append((title, f"{p.name}/index.html"))
    resources.sort(key=lambda x: x[0].lower())
    return resources

def update_readme(resources: list[tuple[str,str]]):
    readme_text = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"{re.escape(BEGIN)}.*?{re.escape(END)}",
        re.S,
    )
    generated_lines = [BEGIN]
    for title, url in resources:
        generated_lines.append(f"- [{title}]({url})")
    generated_lines.append(END)
    new_block = "\n".join(generated_lines)
    new_readme = pattern.sub(new_block, readme_text)
    README_PATH.write_text(new_readme, encoding="utf-8")

if __name__ == "__main__":
    update_readme(gather_resources())
