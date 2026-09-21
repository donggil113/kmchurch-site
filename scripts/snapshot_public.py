"""Capture public kmchurch.kr pages as a local, reviewable static archive.

This intentionally captures public presentation only. Member records, posting,
search, and administration require an authorized database and upload backup.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"
ASSETS = ROOT / "assets" / "archive"
BASE = "http://kmchurch.kr"
GROUPS = [
    ("교회소개", [(1, "위임목사 인사말"), (78, "이번주일 설교"), (2, "비전과 섬김"), (4, "교역자"), (5, "장로"), (6, "직원"), (7, "교회역사"), (8, "교회주보"), (9, "예배시간"), (10, "새가족등록안내"), (11, "새가족앨범"), (12, "오시는 길")]),
    ("말씀과 찬양", [(13, "주일예배"), (16, "수요예배"), (19, "찬양대 예배찬양"), (17, "특별설교&강의"), (18, "특별찬양&행사"), (51, "행사영상")]),
    ("양육과 훈련", [(20, "양육훈련과정"), (81, "수료소감"), (21, "신앙아카데미"), (38, "목양팀")]),
    ("다음세대", []),
    ("선교와 사역", [(33, "국내선교/해외선교"), (39, "중보기도"), (82, "온라인 중보기도"), (29, "예배사역"), (44, "IT미디어"), (30, "새가족/바나바"), (34, "청솔대학/긍휼사역"), (35, "청솔앨범"), (31, "홍보출판")]),
    ("교제와 섬김", [(46, "광명공지"), (79, "줌 및 스마트요람 설치"), (87, "광명앨범"), (48, "온라인행정"), (84, "교우사업체"), (43, "경조"), (36, "관리(시설/차량)"), (41, "사역지원"), (37, "사랑의 식탁")]),
]
ALL_CODES = {code for _, items in GROUPS for code, _ in items}
BOARD_CODES = {8, 11, 81, 82, 35, 46, 87, 48, 84}
VIDEO_CODES = {13, 16, 19, 17, 18, 51, 78}
FIRST = {group: (items[0][0] if items else None) for group, items in GROUPS}
session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (compatible; PublicSiteMigration/1.0)"


def get(url: str) -> str:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.content.decode("utf-8", errors="replace")


def download_asset(value: str) -> str:
    url = urljoin(BASE, value)
    parsed = urlparse(url)
    if parsed.hostname not in {"kmchurch.kr", "www.kmchurch.kr"}:
        return value
    path = parsed.path
    if not (path.startswith("/user/") or path.startswith("/core/")):
        return value
    destination = ASSETS / path.lstrip("/")
    if not destination.exists():
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(response.content)
        except requests.RequestException as exc:
            print(f"asset failed: {url}: {exc}")
            return value
    return "../assets/archive" + path


def local_link(value: str) -> str:
    parsed = urlparse(urljoin(BASE, value))
    if parsed.hostname not in {"kmchurch.kr", "www.kmchurch.kr"}:
        return value
    query = parse_qs(parsed.query)
    if "pageCode" in query:
        try:
            code = int(query["pageCode"][0])
            if code in ALL_CODES and "Mode" not in query:
                return f"{code}.html"
        except ValueError:
            pass
    if "mstrCode" in query:
        try:
            index = int(query["mstrCode"][0]) - 1
            target = FIRST[GROUPS[index][0]]
            if target:
                return f"{target}.html"
        except (ValueError, IndexError):
            pass
    return urljoin(BASE, value)


def clean_fragment(fragment: BeautifulSoup, retain_positioned: bool) -> str:
    for node in fragment.select("script, link, noscript, form, input, button"):
        node.decompose()
    for tag in fragment.find_all(True):
        for attribute in list(tag.attrs):
            if attribute.lower().startswith("on"):
                del tag.attrs[attribute]
        if tag.name == "a" and tag.get("href"):
            href = tag["href"]
            if href.startswith("javascript:"):
                tag.unwrap()
                continue
            tag["href"] = local_link(href)
        for attr in ("src", "poster"):
            if tag.get(attr):
                tag[attr] = download_asset(tag[attr])
        if tag.get("style"):
            tag["style"] = re.sub(
                r"url\((['\"]?)([^)\'\"]+)\1\)",
                lambda match: "url('" + download_asset(match.group(2)) + "')",
                tag["style"],
            )
            if not retain_positioned:
                tag["style"] = re.sub(r"(?:position|top|left|right|bottom|width|height|float)\s*:[^;]+;?", "", tag["style"], flags=re.I)
    return str(fragment)


def content_for(code: int, source: str) -> tuple[str, str]:
    awc = re.search(r"new awcDisplay\((\d+)", source)
    if awc:
        response = session.post(
            BASE + "/core/xml/awc/awcDisplay.xml.html",
            data={"action": "getXML", "pageKey": "0", "pageCode": code, "deviceType": "P"},
            timeout=30,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.content.decode("utf-8", errors="replace"), "html.parser")
        canvas = soup.select_one(".awcBaseLayer")
        if canvas:
            return "canvas", clean_fragment(canvas, True)
    soup = BeautifulSoup(source, "html.parser")
    content = soup.select_one("#awdDisplayContent")
    if not content:
        return "empty", "<p>공개 본문을 확인하지 못했습니다.</p>"
    if code in {4, 5, 6}:
        photos = list(dict.fromkeys(re.findall(r"/user/saveDir/people/[^)\'\" ]+", str(content))))
        label = {4: "교역자", 5: "장로", 6: "직원"}[code]
        cards = ''.join(f'<figure><img src="{html.escape(download_asset(photo), quote=True)}" alt="{label} 사진"></figure>' for photo in photos)
        return "people", cards or "<p>등록된 사진이 없습니다.</p>"
    if code in BOARD_CODES or code in VIDEO_CODES:
        entries = {}
        for link in content.select('a[href*="Mode=view"]'):
            href = link.get("href", "")
            if not href.startswith("/main/sub.html?"):
                continue
            text = link.get_text(" ", strip=True)
            if text and not text.startswith("eyJ") and len(text) < 200:
                entry = entries.setdefault(href, {"title": "", "image": ""})
                if len(text) > len(entry["title"]):
                    entry["title"] = text
                parent = link.find_parent(class_="mdAlbumBox") or link.find_parent("tr")
                if parent:
                    photo = parent.select_one('[style*="background:"]')
                    if photo:
                        match = re.search(r"url\((['\"]?)([^)\'\"]+)\1\)", photo.get("style", ""))
                        if match:
                            entry["image"] = match.group(2)
                    image = parent.find("img")
                    if not entry["image"] and image and image.get("src"):
                        entry["image"] = image["src"]
        cards = []
        for href, entry in list(entries.items())[:30]:
            if not entry["title"]:
                continue
            image = f'<img src="{html.escape(download_asset(entry["image"]), quote=True)}" alt="">' if entry["image"] else ""
            cards.append(f'<a class="archive-card" href="{html.escape(urljoin(BASE, href), quote=True)}">{image}<strong>{html.escape(entry["title"])}</strong></a>')
        if cards:
            return "listing", "".join(cards)
    for node in content.select("style, iframe"):
        node.decompose()
    clean_fragment(content, False)
    # The source uses hidden encoded form values and decorative empty boxes.
    for node in content.select("[style*='display:none'], [style*='display: none']"):
        node.decompose()
    return "document", str(content)


def header_nav() -> str:
    parts = []
    for group, items in GROUPS:
        if group == "다음세대":
            parts.append('<a href="https://km-edu.kr/">다음세대</a>')
        else:
            parts.append(f'<a href="{items[0][0]}.html">{html.escape(group)}</a>')
    return "".join(parts)


def page_html(code: int, title: str, group: str, kind: str, body: str) -> str:
    current_items = next(items for name, items in GROUPS if name == group)
    sidebar = "".join(f'<a href="{item_code}.html" class="{"active" if item_code == code else ""}">{html.escape(label)}</a>' for item_code, label in current_items)
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)} | 광명교회</title><link rel="stylesheet" href="../styles.css"><link rel="stylesheet" href="../archive.css"><link rel="stylesheet" href="../listing.css"><script src="../app.js" defer></script></head>
<body class="subpage"><a class="skip-link" href="#main">본문으로 건너뛰기</a>
<header class="site-header"><div class="header-inner"><a class="brand" href="../" aria-label="광명교회 홈"><img src="../assets/image_122330.png" alt="광명교회"></a><nav class="desktop-nav" aria-label="주 메뉴">{header_nav()}</nav><button class="menu-toggle" type="button" aria-label="전체 메뉴 열기" aria-controls="site-menu" aria-expanded="false"><span></span><span></span><span></span></button></div></header>
<section class="sub-hero"><div><small>2026 광명교회</small><strong>하나님의 사랑, 우리의 삶으로</strong></div></section>
<main id="main" class="sub-layout container"><aside class="sub-sidebar"><h2>{html.escape(group)}</h2>{sidebar}</aside><article class="sub-content"><div class="sub-breadcrumb"><a href="../">HOME</a> / {html.escape(group)} / {html.escape(title)}</div><h1>{html.escape(title)}</h1><div class="archive-{kind}">{body}</div></article></main>
<footer class="site-footer"><div class="container footer-inner"><div><strong>대한예수교장로회(통합) 광명교회</strong><p>경기도 광명시 하안로 437<br>TEL. 02-2686-3311<br>FAX : 02-2686-3322</p><small>COPYRIGHT (C) 광명교회. All Rights Reserved.</small></div><nav aria-label="하단 메뉴"><a href="../">홈</a><a href="../sitemap.html">사이트맵</a></nav></div></footer>
<div class="menu-overlay" id="site-menu" hidden><div class="menu-panel" role="dialog" aria-modal="true" aria-label="전체 메뉴"><div class="menu-top"><img src="../assets/image_122330.png" alt="광명교회"><button class="menu-close" type="button" aria-label="전체 메뉴 닫기">×</button></div><div class="menu-columns">{''.join(f'<div><h2>{html.escape(name)}</h2>'+''.join(f'<a href="{c}.html">{html.escape(label)}</a>' for c,label in items)+'</div>' for name,items in GROUPS)}</div></div></div>
</body></html>'''


def main() -> None:
    PAGES.mkdir(exist_ok=True)
    banner = ASSETS / "user/saveDir/awd/P/0/slideImage_122194_973891.6568754854_0.jpg"
    if not banner.exists():
        download_asset(BASE + "/user/saveDir/awd/P/0/slideImage_122194_973891.6568754854_0.jpg")
    for group, items in GROUPS:
        for code, title in items:
            try:
                source = get(f"{BASE}/main/sub.html?pageCode={code}")
                kind, body = content_for(code, source)
                (PAGES / f"{code}.html").write_text(page_html(code, title, group, kind, body), encoding="utf-8")
                print(f"{code}: {title} ({kind}, {len(body)} chars)")
            except Exception as exc:
                print(f"{code}: ERROR {exc}")
    sections = []
    for group, items in GROUPS:
        links = ''.join(f'<a href="pages/{code}.html">{html.escape(label)}</a>' for code, label in items)
        if group == "다음세대":
            links = '<a href="https://km-edu.kr/">광명다음세대</a><a href="https://momtomom.or.kr/">아름다운 가정세우기</a>'
        sections.append(f'<section><h2>{html.escape(group)}</h2>{links}</section>')
    sitemap = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>사이트맵 | 광명교회</title><link rel="stylesheet" href="styles.css"><link rel="stylesheet" href="listing.css"></head><body class="sitemap-page"><main class="container"><a href="./">← 광명교회 홈</a><h1>사이트맵</h1><div class="sitemap-grid">{"".join(sections)}</div></main></body></html>'''
    (ROOT / "sitemap.html").write_text(sitemap, encoding="utf-8")


if __name__ == "__main__":
    main()
