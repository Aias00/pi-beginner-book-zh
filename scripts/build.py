"""Build the chapter website; optionally regenerate EPUB from the same manuscript."""

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
REPOSITORY = "https://github.com/Aias00/pi-beginner-book-zh"
BASE_URL = "https://aias00.github.io/pi-beginner-book-zh/"
SOURCE_COMMIT = "16f5f0af4d85ca583d045ceb5ed6d646fcaf7761"
TITLE = "从零读懂 Pi"
SUBTITLE = "AI 编程助手的工程入门"


@dataclass(frozen=True)
class Chapter:
    path: Path
    title: str
    label: str
    text: str

    @property
    def url(self) -> str:
        return f"chapters/{self.path.stem}.html"


class Sections(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.entries: list[tuple[str, str]] = []
        self.capture = False
        self.parts: list[str] = []
        self.current_id = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "section":
            self.stack.append(values.get("id") or "")
        if tag == "h2":
            self.capture = True
            self.parts = []
            self.current_id = values.get("id") or (self.stack[-1] if self.stack else "")

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h2":
            if self.current_id:
                self.entries.append((self.current_id, "".join(self.parts)))
            self.capture = False
        if tag == "section" and self.stack:
            self.stack.pop()


def chapters() -> list[Chapter]:
    result = []
    for path in sorted((ROOT / "chapters").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        heading = re.search(r"^# (.+?)(?: \{#[^}]+\})?$", text, re.M)
        if heading is None:
            raise ValueError(f"Missing chapter title: {path}")
        index = int(path.name[:2])
        label = "前言" if index == 0 else (f"{index:02}" if index <= 16 else chr(65 + index - 17))
        result.append(Chapter(path, heading.group(1), label, text))
    if len(result) != 20:
        raise ValueError("Expected preface, 16 chapters and 3 appendices")
    return result


def assemble(items: list[Chapter]) -> tuple[str, str]:
    metadata = (ROOT / "book-meta.yaml").read_text(encoding="utf-8").strip()
    body = "\n\n".join(chapter.text.strip() for chapter in items) + "\n"
    manuscript = f"---\n{metadata}\n---\n\n{body}"
    (ROOT / "book.md").write_text(manuscript, encoding="utf-8")
    return manuscript, body


def generate_epub(items: list[Chapter], manuscript: str, body: str, highlight_option: str) -> None:
    common = ["pandoc", "book.md", "--from=markdown", "--standalone", "--toc", "--toc-depth=2", highlight_option, "--resource-path=.", "--data-dir=assets/pandoc", "--css=assets/book.css", "--fail-if-warnings"]
    subprocess.run(common + ["--to=epub3", "--split-level=1", "--epub-cover-image=assets/cover.png", "--output=pi-beginner.epub"], cwd=ROOT, check=True)
    subprocess.run(common + ["--to=html5", "--section-divs", "--embed-resources", "--output=pi-beginner.html"], cwd=ROOT, check=True)
    stats = json.loads((ROOT / "book-info.json").read_text(encoding="utf-8"))
    stats.update({
        "cjk_characters": len(re.findall(r"[\u3400-\u9fff]", body)),
        "chapter_characters": {chapter.path.name: len(re.findall(r"[\u3400-\u9fff]", chapter.text)) for chapter in items},
        "epub_sha256": hashlib.sha256((ROOT / "pi-beginner.epub").read_bytes()).hexdigest(),
        "epub_bytes": (ROOT / "pi-beginner.epub").stat().st_size,
        "epub_source_sha256": hashlib.sha256(manuscript.encode()).hexdigest(),
    })
    (ROOT / "book-info.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sidebar(items: list[Chapter], prefix: str, current: str) -> str:
    links = []
    for chapter in items:
        active = ' aria-current="page"' if chapter.url == current else ""
        short_title = re.sub(r"^(第[一二三四五六七八九十]+章 |附录 [ABC] |前言：)", "", chapter.title)
        links.append(f'<li><a href="{prefix}{chapter.url}"{active}><span class="chapter-number">{chapter.label}</span><span>{html.escape(short_title)}</span></a></li>')
    return f'''<aside class="sidebar" id="book-nav"><div class="sidebar-heading">全书目录</div>
<nav aria-label="章节目录"><ol class="chapter-list">{"".join(links)}</ol></nav>
<div class="source-note">16 章 · 3 个附录<br>基于 Pi 源码快照<br><a href="https://github.com/earendil-works/pi/tree/{SOURCE_COMMIT}">{SOURCE_COMMIT[:9]}</a></div></aside>'''


def page(items: list[Chapter], current: str, title: str, content: str, is_home: bool = False) -> str:
    prefix = "./" if is_home else "../"
    description = "面向零基础读者，16 章理解 Pi 的使用、模型与工具循环、会话、扩展和源码。支持在线分章阅读和 EPUB 下载。"
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · {TITLE}</title><meta name="description" content="{description}">
<meta name="theme-color" content="#173c4b"><meta name="color-scheme" content="light dark">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{description}">
<meta property="og:type" content="book"><meta property="og:image" content="{BASE_URL}assets/cover.png">
<link rel="canonical" href="{BASE_URL}{current}"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/site.css"><script src="{prefix}assets/site.js" defer></script></head>
<body class="{'home' if is_home else 'reader'}" data-page="{current}" data-title="{html.escape(title, quote=True)}" data-root="{prefix}">
<a class="skip-link" href="#main">跳至正文</a>
<header class="site-header"><a class="brand" href="{prefix}index.html"><span class="brand-mark">Pi</span><span>{TITLE}<small>{SUBTITLE}</small></span></a>
<div class="header-actions"><a class="download-link" href="{prefix}downloads/pi-beginner.epub" download>下载 EPUB</a><a class="repo-link" href="{REPOSITORY}">GitHub</a>
<button id="theme-toggle" type="button" aria-label="切换深色模式" hidden>深色</button><button id="menu-toggle" type="button" aria-controls="book-nav" aria-expanded="false" hidden>目录</button></div></header>
<div class="layout">{sidebar(items, prefix, current)}<main class="main-content" id="main">{content}</main></div>
<footer class="site-footer">基于 Pi 源码的中文学习读物 · 非官方 · AI 辅助编写<br><a href="{REPOSITORY}/blob/main/NOTICE.md">来源与署名</a> · <a href="{REPOSITORY}/blob/main/LICENSES/pi-MIT.txt">Pi 原项目许可</a> · <a href="{prefix}downloads/pi-beginner.epub" download>离线阅读</a></footer></body></html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epub", action="store_true", help="Also regenerate the EPUB and offline HTML")
    args = parser.parse_args()
    if shutil.which("pandoc") is None:
        raise SystemExit("Pandoc is required. See README.md for setup.")
    pandoc_help = subprocess.run(["pandoc", "--help"], text=True, capture_output=True, check=True).stdout
    highlight_option = "--syntax-highlighting=none" if "--syntax-highlighting" in pandoc_help else "--no-highlight"
    items = chapters()
    manuscript, body = assemble(items)
    if args.epub:
        generate_epub(items, manuscript, body, highlight_option)
    stats = json.loads((ROOT / "book-info.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(manuscript.encode()).hexdigest()
    if stats.get("epub_source_sha256") != digest:
        raise SystemExit("Manuscript changed: run python3 scripts/build.py --epub before publishing.")
    if stats["epub_sha256"] != hashlib.sha256((ROOT / "pi-beginner.epub").read_bytes()).hexdigest():
        raise SystemExit("EPUB checksum does not match book-info.json")
    for folder in (SITE, SITE / "chapters", SITE / "assets", SITE / "downloads"):
        folder.mkdir(parents=True, exist_ok=True)
    for name in ("cover.png", "architecture.png", "tool-loop.png", "session-tree.png"):
        shutil.copyfile(ROOT / "assets" / name, SITE / "assets" / name)
    for name in ("site.css", "site.js", "favicon.svg"):
        shutil.copyfile(ROOT / "web" / name, SITE / "assets" / name)
    shutil.copyfile(ROOT / "pi-beginner.epub", SITE / "downloads/pi-beginner.epub")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    cards = "".join(f'<a class="chapter-card" href="{chapter.url}"><span class="chapter-number">{chapter.label}</span><strong>{html.escape(chapter.title)}</strong><span aria-hidden="true">→</span></a>' for chapter in items)
    intro = f'''<section class="hero"><div class="hero-copy"><p class="eyebrow">写给第一次读工程的你</p><h1>{TITLE}</h1><p class="lede">跟着一次任务，理解 AI 编程助手如何读取文件、调用模型、执行工具，并保存工作。</p>
<div class="hero-actions"><a class="primary-button" href="{items[0].url}">开始阅读 <span aria-hidden="true">→</span></a><a class="secondary-button" id="resume-reading" hidden>继续上次阅读</a></div>
<dl class="book-stats"><div><dt>16</dt><dd>循序渐进的章节</dd></div><div><dt>约 4 万</dt><dd>中文讲解</dd></div><div><dt>48</dt><dd>练习与参考答案</dd></div></dl></div><img class="cover" src="assets/cover.png" alt="《从零读懂 Pi：AI 编程助手的工程入门》封面" width="1600" height="2400"></section>
<section class="learning-path"><p class="eyebrow">不必一次读懂所有代码</p><h2>选一条适合你的阅读路线</h2><div class="path-grid">
<a class="path-card" href="{items[1].url}"><span>01 — 04</span><h3>先认识，再使用</h3><p>从终端和基本概念开始，认识工程目录，完成第一次使用。</p></a>
<a class="path-card" href="{items[5].url}"><span>05 — 13</span><h3>跟着任务看内部</h3><p>理解模型与工具循环、会话、扩展，以及持久化和远程执行。</p></a>
<a class="path-card" href="{items[14].url}"><span>14 — 16</span><h3>开始自己读源码</h3><p>沿入口追踪一条调用链，学习检查、测试和排错方法。</p></a></div></section>
<section id="all-chapters"><p class="eyebrow">从一个小问题开始</p><h2>全书目录</h2><div class="chapter-grid">{cards}</div></section>'''
    (SITE / "index.html").write_text(page(items, "index.html", f"{TITLE}：{SUBTITLE}", intro, True), encoding="utf-8")

    for index, chapter in enumerate(items):
        result = subprocess.run(["pandoc", "--from=markdown", "--to=html5", "--section-divs", highlight_option, "--wrap=none"], input=chapter.text, text=True, capture_output=True, check=True)
        article = result.stdout.replace('src="assets/', 'src="../assets/')
        sections = Sections()
        sections.feed(article)
        local_toc = "".join(f'<li><a href="#{html.escape(anchor, quote=True)}">{html.escape(text)}</a></li>' for anchor, text in sections.entries)
        previous = items[index - 1] if index > 0 else None
        following = items[index + 1] if index + 1 < len(items) else None
        previous_link = f'<a class="prev" href="../{previous.url}"><span>上一章</span><strong>{html.escape(previous.title)}</strong></a>' if previous else '<a class="prev" href="../index.html"><span>返回</span><strong>本书首页</strong></a>'
        next_link = f'<a class="next" href="../{following.url}"><span>下一章</span><strong>{html.escape(following.title)}</strong></a>' if following else '<a class="next" href="../index.html"><span>读完了</span><strong>返回全书目录</strong></a>'
        content = f'''<div class="reading-topline"><span class="eyebrow">{html.escape(chapter.label)} · 在线阅读</span><div class="font-controls"><button id="font-decrease" type="button" aria-label="缩小正文字号" hidden>A−</button><button id="font-increase" type="button" aria-label="放大正文字号" hidden>A+</button></div></div>
<details class="on-this-page"><summary>本章小节</summary><nav aria-label="本章小节"><ol>{local_toc}</ol></nav></details>
<article class="prose">{article}</article><nav class="chapter-pagination" aria-label="翻页">{previous_link}{next_link}</nav>'''
        (SITE / chapter.url).write_text(page(items, chapter.url, chapter.title, content), encoding="utf-8")
    urls = ["index.html"] + [chapter.url for chapter in items]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f'<url><loc>{BASE_URL}{url}</loc></url>' for url in urls) + "</urlset>\n"
    (SITE / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n", encoding="utf-8")
    print(f"Built homepage, {len(items)} chapter pages and EPUB download in {SITE}")


if __name__ == "__main__":
    main()
