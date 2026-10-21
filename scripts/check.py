"""Check generated navigation, local resources, manuscript and EPUB integrity."""

import hashlib
import json
import posixpath
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from zipfile import ZIP_STORED, ZipFile

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"


class Document(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.lang = ""
        self.current_links = 0
        self.main = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "html":
            self.lang = data.get("lang") or ""
        if "id" in data:
            identifier = data["id"] or ""
            assert identifier not in self.ids, f"Duplicate ID: {identifier}"
            self.ids.add(identifier)
        if tag == "main":
            self.main = True
        if data.get("aria-current") == "page":
            self.current_links += 1
        if tag == "img":
            assert data.get("alt"), "Missing image alt text"
        for name in ("href", "src"):
            if data.get(name):
                if name == "src":
                    assert not urlsplit(data[name]).scheme, "Required resource must be local"
                self.links.append(data[name])


def main() -> None:
    documents: dict[Path, Document] = {}
    for path in SITE.rglob("*.html"):
        parser = Document()
        parser.feed(path.read_text(encoding="utf-8"))
        assert parser.lang == "zh-CN" and parser.main, path
        documents[path] = parser
    sources = sorted((ROOT / "chapters").glob("*.md"))
    expected = {SITE / "index.html"} | {SITE / "chapters" / f"{path.stem}.html" for path in sources}
    assert set(documents) == expected and len(sources) == 20
    checked_links = 0
    for path, document in documents.items():
        assert document.current_links == (0 if path.name == "index.html" else 1), path
        for value in document.links:
            link = urlsplit(value)
            if link.scheme:
                assert link.scheme == "https", (path, value)
                continue
            assert not link.netloc and not link.path.startswith("/"), (path, value)
            target = (path.parent / unquote(link.path)).resolve() if link.path else path
            assert target.is_relative_to(SITE.resolve()) and target.is_file(), (path, value)
            if link.fragment:
                assert target in documents and unquote(link.fragment) in documents[target].ids, (path, value)
            checked_links += 1
    epub = ROOT / "pi-beginner.epub"
    stats = json.loads((ROOT / "book-info.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(epub.read_bytes()).hexdigest() == stats["epub_sha256"]
    assert epub.read_bytes() == (SITE / "downloads/pi-beginner.epub").read_bytes()
    assert hashlib.sha256((ROOT / "book.md").read_bytes()).hexdigest() == stats["epub_source_sha256"]
    main_chapters = [path for path in sources if 1 <= int(path.name[:2]) <= 16]
    assert len(main_chapters) == 16
    for path in main_chapters:
        text = path.read_text(encoding="utf-8")
        assert len(re.findall(r"[\u3400-\u9fff]", text)) >= 1500 and text.count("参考答案：") == 3, path
    with ZipFile(epub) as archive:
        assert archive.testzip() is None
        assert archive.infolist()[0].filename == "mimetype" and archive.infolist()[0].compress_type == ZIP_STORED
        assert archive.read("mimetype") == b"application/epub+zip"
        members = set(archive.namelist())
        ids = {}
        xml_documents = {}
        for name in members:
            if name.endswith((".xhtml", ".xml", ".opf", ".ncx")):
                tree = ET.fromstring(archive.read(name))
                xml_documents[name] = tree
                identifiers = [element.attrib["id"] for element in tree.iter() if "id" in element.attrib]
                assert len(identifiers) == len(set(identifiers)), name
                ids[name] = set(identifiers)
        for name, tree in xml_documents.items():
            if not name.endswith(".xhtml"):
                continue
            for element in tree.iter():
                for attribute in ("src", "href", "{http://www.w3.org/1999/xlink}href"):
                    if attribute not in element.attrib:
                        continue
                    link = urlsplit(element.attrib[attribute])
                    if link.scheme:
                        continue
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(link.path))) if link.path else name
                    assert target in members, (name, target)
                    if link.fragment:
                        assert unquote(link.fragment) in ids[target], (name, target, link.fragment)
    print(f"Passed: {len(documents)} pages, {checked_links} local links/resources, 16 chapters, 48 answers, EPUB integrity and manuscript synchronization")


if __name__ == "__main__":
    main()
