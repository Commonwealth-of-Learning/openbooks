"""Moodle backup (.mbz) converter.

This module provides a command line interface that can unpack a Moodle
backup, translate supported HTML-based activities to Markdown, copy any
binary assets, and emit a lightweight manifest that downstream tooling
can consume.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
from markdownify import markdownify

PACKAGE_ROOT = Path(__file__).resolve().parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.append(str(PACKAGE_ROOT))

from utils import setup_logging


@dataclass
class ModuleRecord:
    """Represents a Moodle activity within a section."""

    module_id: str
    module_type: str
    title: str
    directory: str
    visible: bool = True
    summary: str = ""


@dataclass
class SectionRecord:
    """Represents a section/topic in the Moodle course."""

    index: int
    title: str
    summary: str
    modules: List[ModuleRecord] = field(default_factory=list)


class MoodleBackupConverter:
    """Converter responsible for processing Moodle backup archives."""

    SUPPORTED_HTML_MODULES = {"page", "label", "book"}
    SUPPORTED_FILE_MODULES = {"resource"}

    def __init__(
        self,
        mbz_path: Path,
        output_dir: Path,
        include_hidden: bool = False,
        clean_html: bool = True,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.mbz_path = Path(mbz_path)
        self.output_dir = Path(output_dir)
        self.include_hidden = include_hidden
        self.clean_html = clean_html
        self.logger = logger or logging.getLogger(__name__)

        self.content_dir = self.output_dir / "content"
        self.assets_dir = self.output_dir / "assets"

        self.asset_index_by_hash: Dict[str, str] = {}
        self.asset_index_by_name: Dict[str, List[str]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def convert(self) -> None:
        """Execute the conversion workflow."""

        if not self.mbz_path.exists():
            raise FileNotFoundError(f"Backup not found: {self.mbz_path}")

        self.logger.info("Starting Moodle backup conversion for %s", self.mbz_path)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.content_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        with TemporaryDirectory() as tmp_dir:
            extract_dir = Path(tmp_dir)
            self._extract_backup(extract_dir)

            course_info = self._parse_course_information(extract_dir)
            sections = self._parse_sections(extract_dir)

            asset_manifest = self._prepare_assets(extract_dir)

            manifest_sections, summary_entries = self._process_sections(
                extract_dir, course_info, sections
            )

            self._write_index(course_info, sections)
            self._write_summary(summary_entries)
            self._write_manifest(course_info, manifest_sections, asset_manifest)

        self.logger.info("Conversion finished. Output available at %s", self.output_dir)

    # ------------------------------------------------------------------
    # Extraction and parsing helpers
    # ------------------------------------------------------------------
    def _extract_backup(self, destination: Path) -> None:
        """Unzip the .mbz archive to a temporary folder."""

        self.logger.debug("Extracting backup to %s", destination)
        with zipfile.ZipFile(self.mbz_path, "r") as archive:
            archive.extractall(destination)

    def _parse_course_information(self, extract_dir: Path) -> Dict[str, Any]:
        """Read high-level course information from moodle_backup.xml."""

        backup_xml = extract_dir / "moodle_backup.xml"
        course_info: Dict[str, Any] = {
            "fullname": "",
            "shortname": "",
            "summary": "",
            "original_course_id": "",
        }

        if not backup_xml.exists():
            self.logger.warning("moodle_backup.xml not found in archive")
            return course_info

        tree = ET.parse(backup_xml)
        information = tree.find(".//information")
        if information is None:
            return course_info

        def _text(elem_name: str) -> str:
            value = information.findtext(elem_name, default="")
            return value.strip() if value else ""

        course_info["fullname"] = _text("original_course_fullname") or _text(
            "course_fullname"
        )
        course_info["shortname"] = _text("original_course_shortname") or _text(
            "course_shortname"
        )
        course_info["summary"] = _text("details")
        course_info["original_course_id"] = _text("original_course_id")

        return course_info

    def _parse_sections(self, extract_dir: Path) -> List[SectionRecord]:
        """Parse section metadata to preserve ordering and membership."""

        sections_root = extract_dir / "sections"
        if not sections_root.exists():
            self.logger.warning("No sections directory found in backup")
            return []

        section_records: List[SectionRecord] = []
        section_dirs = sorted(
            (p for p in sections_root.iterdir() if p.is_dir()),
            key=lambda p: self._extract_numeric_suffix(p.name),
        )

        for section_dir in section_dirs:
            section_xml = section_dir / "section.xml"
            if not section_xml.exists():
                self.logger.debug("Skipping section without section.xml: %s", section_dir)
                continue

            tree = ET.parse(section_xml)
            section_elem = tree.getroot().find("section") or tree.getroot()

            index = int(self._safe_int(section_elem.findtext("number"), default=len(section_records)))
            title = (section_elem.findtext("title") or section_elem.findtext("name") or "Untitled Section").strip()
            summary = (section_elem.findtext("summary") or "").strip()

            modules: List[ModuleRecord] = []
            for module_elem in section_elem.findall(".//module"):
                module_type = (module_elem.findtext("modulename") or "").strip()
                module_id = (
                    module_elem.findtext("moduleid")
                    or module_elem.findtext("id")
                    or module_elem.findtext("module")
                    or ""
                ).strip()
                title_text = (
                    module_elem.findtext("title")
                    or module_elem.findtext("name")
                    or module_type.title()
                ).strip()
                visible_text = module_elem.findtext("visible") or "1"
                visible = visible_text.strip() != "0"

                if not module_type or not module_id:
                    self.logger.debug(
                        "Skipping malformed module entry in section %s", section_dir.name
                    )
                    continue

                if not visible and not self.include_hidden:
                    self.logger.info(
                        "Skipping hidden module %s (%s)", title_text, module_type
                    )
                    continue

                directory = f"{module_type}_{module_id}"
                modules.append(
                    ModuleRecord(
                        module_id=module_id,
                        module_type=module_type,
                        title=title_text,
                        directory=directory,
                        visible=visible,
                    )
                )

            section_records.append(
                SectionRecord(index=index, title=title, summary=summary, modules=modules)
            )

        section_records.sort(key=lambda s: s.index)
        return section_records

    # ------------------------------------------------------------------
    # Asset management
    # ------------------------------------------------------------------
    def _prepare_assets(self, extract_dir: Path) -> List[Dict[str, Any]]:
        """Copy files from the Moodle archive into the assets directory."""

        files_root = extract_dir / "files"
        files_xml = extract_dir / "files.xml"
        metadata: Dict[str, Dict[str, Any]] = {}

        if files_xml.exists():
            tree = ET.parse(files_xml)
            for file_elem in tree.findall(".//file"):
                contenthash = (file_elem.findtext("contenthash") or "").strip()
                if not contenthash:
                    continue
                metadata[contenthash] = {
                    "filename": (file_elem.findtext("filename") or "").strip(),
                    "filepath": (file_elem.findtext("filepath") or "").strip("/"),
                    "component": (file_elem.findtext("component") or "").strip(),
                    "filearea": (file_elem.findtext("filearea") or "").strip(),
                    "itemid": (file_elem.findtext("itemid") or "").strip(),
                }

        manifest: List[Dict[str, Any]] = []
        if not files_root.exists():
            return manifest

        for source_path in sorted(files_root.rglob("*")):
            if not source_path.is_file():
                continue

            hash_name = source_path.name
            meta = metadata.get(hash_name, {})

            dest_rel = self._derive_asset_path(hash_name, meta)
            dest_path = self.assets_dir / dest_rel
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source_path, dest_path)

            rel_str = dest_rel.as_posix()
            manifest.append({
                "hash": hash_name,
                "path": rel_str,
                "metadata": meta,
            })

            self.asset_index_by_hash[hash_name] = rel_str

            filename = (meta.get("filename") or dest_path.name).lower()
            self.asset_index_by_name.setdefault(filename, []).append(rel_str)

        return manifest

    def _derive_asset_path(self, hash_name: str, meta: Dict[str, Any]) -> Path:
        """Create a deterministic path inside assets/ for a given file."""

        filename = meta.get("filename") or hash_name
        filepath = meta.get("filepath") or ""
        component = meta.get("component") or "component"
        filearea = meta.get("filearea") or "files"
        itemid = meta.get("itemid") or ""

        safe_parts = [self._sanitize_path(component), self._sanitize_path(filearea)]
        if itemid and itemid != "0":
            safe_parts.append(self._sanitize_path(itemid))
        if filepath:
            for part in Path(filepath).parts:
                if part not in {"."}:
                    safe_parts.append(self._sanitize_path(part))
        safe_parts.append(self._sanitize_path(filename))

        return Path(*safe_parts)

    # ------------------------------------------------------------------
    # Section/module processing
    # ------------------------------------------------------------------
    def _process_sections(
        self,
        extract_dir: Path,
        course_info: Dict[str, Any],
        sections: List[SectionRecord],
    ) -> Tuple[List[Dict[str, Any]], List[Tuple[str, Optional[str], str]]]:
        """Generate Markdown content for each section/module."""

        manifest_sections: List[Dict[str, Any]] = []
        summary_entries: List[Tuple[str, Optional[str], str]] = []
        chapter_counter = 1

        for section in sections:
            section_entry = {
                "index": section.index,
                "title": section.title,
                "summary": section.summary,
                "modules": [],
            }

            section_summary_added = False
            for module in section.modules:
                module_entry, chapter_counter = self._process_module(
                    extract_dir, section, module, chapter_counter
                )

                if module_entry is None:
                    continue

                section_entry["modules"].append(module_entry)

                for file_entry in module_entry.get("files", []):
                    summary_entries.append((section.title, file_entry["title"], file_entry["path"]))
                    section_summary_added = True

            if section_entry["modules"]:
                manifest_sections.append(section_entry)
                if not section_summary_added:
                    summary_entries.append((section.title, None, ""))

        return manifest_sections, summary_entries

    def _process_module(
        self,
        extract_dir: Path,
        section: SectionRecord,
        module: ModuleRecord,
        chapter_counter: int,
    ) -> Tuple[Optional[Dict[str, Any]], int]:
        """Dispatch module processing based on activity type."""

        module_dir = extract_dir / "activities" / module.directory
        if not module_dir.exists():
            self.logger.warning("Module directory missing: %s", module.directory)
            return None, chapter_counter

        processor = None
        if module.module_type in self.SUPPORTED_HTML_MODULES:
            processor = self._process_html_module
        elif module.module_type in self.SUPPORTED_FILE_MODULES:
            processor = self._process_file_module

        if processor is None:
            self.logger.info("Skipping unsupported module type: %s", module.module_type)
            return None, chapter_counter

        return processor(section, module, module_dir, chapter_counter)

    def _process_html_module(
        self,
        section: SectionRecord,
        module: ModuleRecord,
        module_dir: Path,
        chapter_counter: int,
    ) -> Tuple[Optional[Dict[str, Any]], int]:
        """Convert HTML-bearing modules into Markdown chapters."""

        outputs: List[Dict[str, Any]] = []
        used_assets: List[str] = []

        if module.module_type == "book":
            chapter_dirs = sorted(
                (p for p in (module_dir / "chapters").glob("chapter_*")),
                key=lambda p: self._extract_numeric_suffix(p.name),
            )
            for chapter_dir in chapter_dirs:
                chapter_xml = chapter_dir / "chapter.xml"
                if not chapter_xml.exists():
                    continue

                tree = ET.parse(chapter_xml)
                chapter_elem = tree.getroot().find("chapter") or tree.getroot()
                chapter_title = (
                    chapter_elem.findtext("title")
                    or chapter_elem.findtext("name")
                    or module.title
                ).strip()
                html_content = (
                    chapter_elem.findtext("content")
                    or chapter_elem.findtext("content")
                    or ""
                )

                markdown_text, chapter_assets = self._html_to_markdown(html_content)
                used_assets.extend(chapter_assets)

                filename = f"chapter{chapter_counter:02d}.md"
                file_path = self.content_dir / filename
                self._write_markdown(file_path, chapter_title, section.title, module, chapter_counter, markdown_text)

                outputs.append({"path": f"content/{filename}", "title": chapter_title, "order": chapter_counter})
                chapter_counter += 1

        else:
            module_xml = module_dir / f"{module.module_type}.xml"
            if not module_xml.exists():
                self.logger.warning(
                    "Missing XML for module %s (%s)", module.title, module.module_type
                )
                return None, chapter_counter

            tree = ET.parse(module_xml)
            module_elem = tree.getroot().find(module.module_type) or tree.getroot()
            html_content = (
                module_elem.findtext("content")
                or module_elem.findtext("intro")
                or ""
            )

            markdown_text, module_assets = self._html_to_markdown(html_content)
            used_assets.extend(module_assets)

            filename = f"chapter{chapter_counter:02d}.md"
            file_path = self.content_dir / filename
            self._write_markdown(file_path, module.title, section.title, module, chapter_counter, markdown_text)

            outputs.append({"path": f"content/{filename}", "title": module.title, "order": chapter_counter})
            chapter_counter += 1

        if not outputs:
            return None, chapter_counter

        module_entry = {
            "id": module.module_id,
            "type": module.module_type,
            "title": module.title,
            "files": outputs,
            "assets": sorted(set(used_assets)),
        }

        return module_entry, chapter_counter

    def _process_file_module(
        self,
        section: SectionRecord,
        module: ModuleRecord,
        module_dir: Path,
        chapter_counter: int,
    ) -> Tuple[Optional[Dict[str, Any]], int]:
        """Register file-based resources in the manifest and copy assets."""

        module_xml = module_dir / f"{module.module_type}.xml"
        if not module_xml.exists():
            self.logger.warning(
                "Missing XML for module %s (%s)", module.title, module.module_type
            )
            return None, chapter_counter

        tree = ET.parse(module_xml)
        module_elem = tree.getroot().find(module.module_type) or tree.getroot()

        referenced_assets: List[str] = []
        for file_elem in module_elem.findall(".//file"):
            contenthash = (file_elem.findtext("contenthash") or "").strip()
            filename = (file_elem.findtext("filename") or "").strip().lower()
            if contenthash and contenthash in self.asset_index_by_hash:
                referenced_assets.append(self.asset_index_by_hash[contenthash])
            elif filename and filename in self.asset_index_by_name:
                referenced_assets.extend(self.asset_index_by_name[filename])

        referenced_assets = sorted(set(referenced_assets))

        module_entry = {
            "id": module.module_id,
            "type": module.module_type,
            "title": module.title,
            "files": [],
            "assets": referenced_assets,
        }

        if referenced_assets:
            self.logger.info(
                "Registered %d asset(s) for resource %s", len(referenced_assets), module.title
            )
        else:
            self.logger.info("Resource module %s has no linked files", module.title)

        return module_entry, chapter_counter

    # ------------------------------------------------------------------
    # Markdown helpers
    # ------------------------------------------------------------------
    def _html_to_markdown(self, html: str) -> Tuple[str, List[str]]:
        """Sanitize HTML, rewrite asset URLs, and convert to Markdown."""

        soup = BeautifulSoup(html or "", "lxml")

        if self.clean_html:
            for tag in soup(["script", "style"]):
                tag.decompose()

        used_assets: List[str] = []

        def rewrite_attr(tag, attr: str) -> None:
            value = tag.get(attr)
            if not value:
                return
            new_value, asset = self._map_asset(value)
            if new_value:
                tag[attr] = new_value
            if asset:
                used_assets.append(asset)

        for tag in soup.find_all(True):
            if tag.has_attr("src"):
                rewrite_attr(tag, "src")
            if tag.has_attr("href"):
                rewrite_attr(tag, "href")

        markdown_text = markdownify(str(soup), heading_style="ATX")

        return markdown_text.strip(), sorted(set(used_assets))

    def _write_markdown(
        self,
        file_path: Path,
        title: str,
        section_title: str,
        module: ModuleRecord,
        order: int,
        markdown_body: str,
    ) -> None:
        """Persist Markdown with YAML front matter."""

        front_matter = [
            "---",
            f'title: "{self._escape_yaml(title)}"',
            f'section: "{self._escape_yaml(section_title)}"',
            f'module_id: "{self._escape_yaml(module.module_id)}"',
            f'module_type: "{self._escape_yaml(module.module_type)}"',
            f'order: {order}',
            "---",
            "",
        ]

        file_path.write_text("\n".join(front_matter + [markdown_body, ""]), encoding="utf-8")

    # ------------------------------------------------------------------
    # Output helpers
    # ------------------------------------------------------------------
    def _write_index(self, course_info: Dict[str, Any], sections: List[SectionRecord]) -> None:
        """Create a high-level course overview file."""

        lines = ["---", f'title: "{self._escape_yaml(course_info.get("fullname") or "Course Overview")}"', "---", ""]

        course_title = course_info.get("fullname") or "Course Overview"
        lines.append(f"# {course_title}\n")

        shortname = course_info.get("shortname")
        if shortname:
            lines.append(f"**Course code:** {shortname}\n")

        summary = course_info.get("summary")
        if summary:
            lines.append(summary)
            lines.append("")

        if sections:
            lines.append("## Sections\n")
            for section in sections:
                module_count = len(section.modules)
                lines.append(f"- {section.title} ({module_count} module{'s' if module_count != 1 else ''})")

        (self.output_dir / "index.md").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    def _write_summary(self, entries: List[Tuple[str, Optional[str], str]]) -> None:
        """Generate a SUMMARY.md file for GitBook-style navigation."""

        lines = ["# Summary", "", "* [Course Overview](index.md)"]
        current_section: Optional[str] = None

        for section_title, item_title, path in entries:
            if section_title != current_section:
                lines.append(f"* {section_title}")
                current_section = section_title

            if item_title and path:
                lines.append(f"  * [{item_title}]({path})")

        (self.output_dir / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _write_manifest(
        self,
        course_info: Dict[str, Any],
        sections: List[Dict[str, Any]],
        asset_manifest: List[Dict[str, Any]],
    ) -> None:
        """Emit a machine-readable manifest describing the conversion."""

        payload = {
            "course": course_info,
            "sections": sections,
            "assets": asset_manifest,
        }

        (self.output_dir / "manifest.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_numeric_suffix(value: str) -> int:
        match = re.search(r"(\d+)$", value)
        return int(match.group(1)) if match else 0

    @staticmethod
    def _safe_int(value: Optional[str], default: int = 0) -> int:
        try:
            return int(value) if value is not None else default
        except ValueError:
            return default

    @staticmethod
    def _sanitize_path(value: str) -> str:
        sanitized = re.sub(r"[^\w\-/]+", "_", value.strip())
        return sanitized or "item"

    @staticmethod
    def _escape_yaml(value: str) -> str:
        return value.replace("\"", "\\\"")

    def _map_asset(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Resolve an asset reference to a copied file path."""

        if not url:
            return None, None

        if url.startswith("@@PLUGINFILE@@"):
            url = url.replace("@@PLUGINFILE@@", "").lstrip("/")
        elif url.startswith("pluginfile.php"):
            parts = url.split("/")
            url = "/".join(parts[5:]) if len(parts) > 5 else parts[-1]
        elif url.startswith("files/"):
            url = url.split("/", 1)[-1]

        filename = url.split("/")[-1].lower()
        if not filename:
            return None, None

        asset_paths = self.asset_index_by_name.get(filename)
        if not asset_paths:
            return None, None

        asset_path = asset_paths[0]
        return f"../assets/{asset_path}", asset_path


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level CLI parser."""

    parser = argparse.ArgumentParser(description="Moodle backup converter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser("convert", help="Convert a Moodle backup")
    convert_parser.add_argument("--mbz", required=True, type=Path, help="Path to the Moodle .mbz backup file")
    convert_parser.add_argument("--output", required=True, type=Path, help="Directory for converted content")
    convert_parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden activities from the backup",
    )
    convert_parser.add_argument(
        "--no-clean-html",
        action="store_true",
        help="Disable HTML sanitisation before Markdown conversion",
    )
    convert_parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    return parser


def main(argv: Optional[Iterable[str]] = None) -> None:
    """Entry point used by the CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    logger = setup_logging(args.log_level if hasattr(args, "log_level") else "INFO")

    if args.command == "convert":
        converter = MoodleBackupConverter(
            mbz_path=args.mbz,
            output_dir=args.output,
            include_hidden=getattr(args, "include_hidden", False),
            clean_html=not getattr(args, "no_clean_html", False),
            logger=logger,
        )
        converter.convert()


if __name__ == "__main__":
    main()
