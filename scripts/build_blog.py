"""Build static editorial articles and book-introduction series from Markdown.
Production deploys the committed dist directory; Python is an editorial build tool only.
Run: python3 -m pip install -r scripts/requirements.txt && python3 scripts/build_blog.py
"""
from pathlib import Path
from html import escape
import json
import re
import math
import xml.etree.ElementTree as ET
import markdown
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
ORIGIN = 'https://book.allrounder.im'
POSTS = json.loads((ROOT / 'content/blog/posts.json').read_text())
BY_SLUG = {post['slug']: post for post in POSTS}
SERIES = sorted([p for p in POSTS if p.get('kind') == 'book-series'], key=lambda p: p['series_order'])
GUIDES = [p for p in POSTS if p.get('kind') != 'book-series']
LANDING = (DIST / 'index.html').read_text()
SOUP = BeautifulSoup(LANDING, 'html.parser')
STYLE = DIST / 'assets/site.css'
if not STYLE.exists():
    STYLE.write_text(SOUP.style.string.strip() + '\n')
HEADER = re.sub(r'href="#', 'href="/#', str(SOUP.select_one('header.site-head')))
FAVICON = str(SOUP.select_one('link[rel="icon"]'))
TRACKING = str(SOUP.find('script'))
PIXEL = next(str(tag) for tag in SOUP.find_all('script') if "fbq('init'" in (tag.string or ''))
BOOK_IMAGE = ORIGIN + '/assets/book-flat.jpg'
DATE = '2026-10-14'
BOOK = {'@type': 'Book', 'name': 'AI Agent를 지휘하는 마케터', 'author': {'@type': 'Person', 'name': '박충효'}, 'url': ORIGIN + '/'}
GUIDE_DISCLOSURE = 'Command Marketing 편집 콘텐츠 · AI 초안 활용, 공개 출처 기반 편집. 도서 발췌나 저자의 직접 발언이 아닌 실무 응용 콘텐츠입니다. 예시는 실제 캠페인 성과가 아니며 검색 노출과 AI 인용을 보장하지 않습니다.'
SERIES_DISCLOSURE = 'Command Marketing 도서 소개 · AI 초안 활용. 제공된 최종 내지 PDF를 근거로 요약·소개한 편집 콘텐츠이며 저자가 직접 집필한 블로그 글은 아닙니다. 별도 표시한 예시는 편집 응용입니다. 원본 PDF는 공개하지 않습니다.'


def graph_json(data):
    return json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')


def head(title, description, path=None, graph=None, post=None, noindex=False):
    url = ORIGIN + path if path is not None else None
    canonical = f'<link rel="canonical" href="{escape(url, quote=True)}">' if url else ''
    og_url = f'<meta property="og:url" content="{escape(url, quote=True)}">' if url else ''
    image = ORIGIN + post['image_jpg'] if post else BOOK_IMAGE
    image_alt = post['image_alt'] if post else 'AI Agent를 지휘하는 마케터 도서 이미지'
    image_dimensions = '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="675">' if post else ''
    dates = ''
    if post:
        dates = f'<meta property="article:published_time" content="{post["date"]}T00:00:00+09:00"><meta property="article:modified_time" content="{post.get("modified", post["date"])}T00:00:00+09:00">'
    schema = f'<script type="application/ld+json">{graph_json(graph)}</script>' if graph else ''
    return f'''<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} | Command Marketing</title>
<meta name="description" content="{escape(description, quote=True)}">
<meta name="author" content="Command Marketing"><meta name="publisher" content="TROE">
<meta name="robots" content="{'noindex,follow' if noindex else 'index,follow,max-snippet:-1,max-image-preview:large'}">
<meta name="referrer" content="strict-origin-when-cross-origin"><meta name="theme-color" content="#eef3f1">
{canonical}<meta property="og:locale" content="ko_KR"><meta property="og:type" content="{'article' if post else 'website'}">
<meta property="og:site_name" content="Command Marketing"><meta property="og:title" content="{escape(title, quote=True)}">
<meta property="og:description" content="{escape(description, quote=True)}">{og_url}
<meta property="og:image" content="{image}"><meta property="og:image:alt" content="{escape(image_alt, quote=True)}">
{image_dimensions}
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(title, quote=True)}">
<meta name="twitter:description" content="{escape(description, quote=True)}"><meta name="twitter:image" content="{image}"><meta name="twitter:image:alt" content="{escape(image_alt, quote=True)}">
{dates}{FAVICON}<link rel="stylesheet" href="/assets/site.css"><link rel="stylesheet" href="/assets/enhancements.css">
<link rel="sitemap" type="application/xml" href="/sitemap.xml"><link rel="describedby" href="/llms.txt">
{TRACKING}{PIXEL}{schema}</head>'''


def breadcrumbs(post=None):
    last = '<span aria-current="page">블로그</span>' if not post else f'<a href="/blog">블로그</a><span aria-hidden="true">/</span><span aria-current="page">{escape(post["title"])}</span>'
    return f'<nav class="breadcrumbs" aria-label="현재 위치"><a href="/">도서 홈</a><span aria-hidden="true">/</span>{last}</nav>'


def breadcrumb_graph(post=None):
    rows = [{'@type': 'ListItem', 'position': 1, 'name': '도서 홈', 'item': ORIGIN + '/'}, {'@type': 'ListItem', 'position': 2, 'name': '블로그', 'item': ORIGIN + '/blog'}]
    if post:
        rows.append({'@type': 'ListItem', 'position': 3, 'name': post['title'], 'item': ORIGIN + '/blog/' + post['slug']})
    return {'@type': 'BreadcrumbList', 'itemListElement': rows}


def picture(post, hero=False):
    attrs = 'fetchpriority="high" loading="eager"' if hero else 'loading="lazy"'
    return f'<picture><source srcset="{post["image"]}" type="image/webp"><img src="{post["image_jpg"]}" alt="{escape(post["image_alt"], quote=True)}" width="1200" height="675" {attrs} decoding="async"></picture>'


def card(post):
    href = '/blog/' + post['slug']
    return f'''<article class="blog-card"><a class="blog-card-cover" href="{href}" data-blog-link="{post['slug']}" aria-label="{escape(post['title'], quote=True)}">{picture(post)}</a>
<p class="eyebrow">{escape(post['category'])} / {post['date']}</p><h3><a href="{href}" data-blog-link="{post['slug']}">{escape(post['title'])}</a></h3>
<p>{escape(post['description'])}</p><a class="text-link" href="{href}" data-blog-link="{post['slug']}">글 읽기 →</a></article>'''


def series_navigation(post):
    if post.get('kind') != 'book-series':
        return ''
    entries = ''.join(f'<li><a href="/blog/{p["slug"]}"' + (' aria-current="page"' if p['slug'] == post['slug'] else '') + f'>{p["series_order"]}. {escape(p["short_title"])}</a></li>' for p in SERIES)
    index = SERIES.index(post)
    previous = f'<a href="/blog/{SERIES[index-1]["slug"]}">← 이전 편: {escape(SERIES[index-1]["short_title"])}</a>' if index else ''
    following = f'<a href="/blog/{SERIES[index+1]["slug"]}">다음 편: {escape(SERIES[index+1]["short_title"])} →</a>' if index + 1 < len(SERIES) else '<a href="/#contents">책 전체 목차 보기 →</a>'
    return f'<nav class="series-nav" aria-label="책 소개 시리즈"><p class="eyebrow">책 소개 시리즈 / {post["series_order"]} of {len(SERIES)}</p><ol>{entries}</ol><div class="series-pager">{previous}{following}</div></nav>'


FOOTER = '''<footer class="blog-footer"><div class="wrap"><a class="text-link" href="/">AI Agent를 지휘하는 마케터</a> · <a href="/blog">블로그</a> · <a href="https://troe.kr/">TROE</a><br>© 2026 TROE. ALL RIGHTS RESERVED.</div></footer><script src="/assets/enhancements.js" defer></script></body></html>'''

for post in POSTS:
    src = (ROOT / 'content/blog' / (post['slug'] + '.md')).read_text()
    assert src.splitlines()[0].removeprefix('# ').strip() == post['title'], post['slug']
    for image_key in ('image', 'image_jpg'):
        assert (DIST / post[image_key].lstrip('/')).is_file(), post[image_key]
    refs = re.findall(r'^\[(\d+)\]:\s+(\S+)\s+"([^"\n]+)"\s*$', src, re.M)
    assert len(refs) >= 2, post['slug']
    source_list = '\n' + '\n'.join(f'{number}. [{escape(title)}]({url})' for number, url, title in refs) + '\n'
    src = src.replace('## References', '## 출처 및 참고 자료\n' + source_list)
    src = re.sub(r'^# .*\n', '', src, count=1)
    rendered = BeautifulSoup(markdown.markdown(src, extensions=['fenced_code', 'tables', 'sane_lists']), 'html.parser')
    toc = []
    for index, heading in enumerate(rendered.find_all('h2'), 1):
        heading['id'] = f'section-{index}'
        toc.append(f'<li><a href="#section-{index}">{escape(heading.get_text())}</a></li>')
    reading = max(3, math.ceil(len(rendered.get_text()) / 650))
    path = '/blog/' + post['slug']
    url = ORIGIN + path
    article = {'@type': 'BlogPosting', '@id': url + '#article', 'mainEntityOfPage': url, 'url': url,
               'headline': post['title'], 'description': post['description'], 'datePublished': post['date'],
               'dateModified': post.get('modified', post['date']), 'inLanguage': 'ko-KR',
               'image': {'@type': 'ImageObject', 'url': ORIGIN + post['image_jpg'], 'width': 1200, 'height': 675, 'caption': post['image_alt']},
               'articleSection': post['category'], 'author': {'@type': 'Organization', 'name': 'Command Marketing', 'url': ORIGIN + '/blog'},
               'publisher': {'@type': 'Organization', 'name': 'TROE', 'url': 'https://troe.kr/'},
               'isPartOf': {'@type': 'Blog', '@id': ORIGIN + '/blog#blog', 'name': 'Command Marketing 블로그'},
               'citation': [ref_url for _, ref_url, _ in refs]}
    is_series = post.get('kind') == 'book-series'
    if is_series:
        article['isBasedOn'] = BOOK
        article['citation'].append(BOOK)
    graph = {'@context': 'https://schema.org', '@graph': [article, breadcrumb_graph(post)]}
    related = ''.join(card(BY_SLUG[slug]) for slug in post['related'])
    disclosure = SERIES_DISCLOSURE if is_series else GUIDE_DISCLOSURE
    date_text = f'게시: <time datetime="{post["date"]}">{post["date"]}</time> · 검토·수정: <time datetime="{post.get("modified", post["date"])}">{post.get("modified", post["date"])}</time>'
    html = head(post['title'], post['description'], path, graph, post=post) + f'''
<body class="blog-page" data-article="{post['slug']}"><a class="skip-link" href="#main">본문으로 이동</a>{HEADER}
<main class="blog-main wrap" id="main">{breadcrumbs(post)}
<header class="blog-heading"><p class="eyebrow">{escape(post['category'])}</p><h1>{escape(post['title'])}</h1>
<p class="article-meta"><span>편집: Command Marketing</span><span>{date_text}</span><span>약 {reading}분 읽기</span></p>
<p class="blog-disclosure">{disclosure}</p></header>
<figure class="article-cover">{picture(post, hero=True)}<figcaption>AI 생성 카툰 · 한국어 손글씨 콘셉트 · 글의 주제를 표현한 편집 일러스트</figcaption></figure>
{series_navigation(post)}
<div class="article-layout"><aside class="article-toc" aria-label="글 목차"><p>이 글의 순서</p><ol>{''.join(toc)}</ol></aside>
<article class="article-body" aria-label="{escape(post['title'], quote=True)}">{str(rendered)}
<div class="article-end" id="article-end"><h2>도구보다 운영 기준을 먼저 세우세요.</h2><p>책의 R-G-C-T-O-R 구조와 3주 훈련을 확인하거나 팀에 적용할 범위를 살펴보세요.</p>
<div class="actions"><a class="button primary" href="/#contents">책 구성 보기</a><a class="button secondary" href="/#consulting" data-consulting-path data-position="blog-article">팀 적용 범위 보기</a></div></div></article></div>
<section class="blog-section" style="padding:40px 0 70px" aria-labelledby="related-title"><h2 class="extra-title" id="related-title">함께 읽으면 좋은 글</h2><div class="blog-cards">{related}</div><a class="text-link" href="/blog">블로그 전체 보기 →</a></section></main>{FOOTER}'''
    directory = DIST / 'blog' / post['slug']
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'index.html').write_text(html)

series_cards = ''.join(card(p) for p in SERIES)
guide_cards = ''.join(card(p) for p in GUIDES)
ordered = SERIES + GUIDES
items = [{'@type': 'ListItem', 'position': i + 1, 'url': ORIGIN + '/blog/' + p['slug'], 'name': p['title']} for i, p in enumerate(ordered)]
graph = {'@context': 'https://schema.org', '@graph': [
    {'@type': 'CollectionPage', '@id': ORIGIN + '/blog#webpage', 'url': ORIGIN + '/blog', 'name': 'AI 마케팅 책 소개와 SEO·GEO·AIEO 실무 블로그', 'inLanguage': 'ko-KR', 'mainEntity': {'@type': 'ItemList', 'itemListElement': items}},
    {'@type': 'Blog', '@id': ORIGIN + '/blog#blog', 'url': ORIGIN + '/blog', 'name': 'Command Marketing 블로그', 'inLanguage': 'ko-KR', 'publisher': {'@type': 'Organization', 'name': 'TROE', 'url': 'https://troe.kr/'}}, breadcrumb_graph()]}
index = head('AI 마케팅 책 소개와 SEO·GEO·AIEO 실무 블로그', 'AI Agent를 지휘하는 마케터 책 소개 시리즈 3편과 SEO·GEO·AIEO 실무 가이드 5편. Agent와 거버넌스, 업무 지시서, 21일 훈련부터 기술 SEO와 AI 검색 성과 측정까지 읽어 보세요.', '/blog', graph) + f'''
<body class="blog-page"><a class="skip-link" href="#main">본문으로 이동</a>{HEADER}<main class="blog-main wrap" id="main">{breadcrumbs()}
<header class="blog-heading"><p class="eyebrow">Command Marketing / Field notes</p><h1>책에서 운영으로,<br>검색에서 답변으로.</h1><p class="section-copy">책 소개 시리즈 3편으로 AI 마케팅의 운영 구조를 읽고, 실무 가이드 5편으로 검색·콘텐츠·검수·측정의 기준을 세우세요.</p><nav class="blog-category-nav" aria-label="블로그 콘텐츠 분류"><a href="#book-series">책 소개 시리즈 3편</a><a href="#practical-guides">SEO·GEO·AIEO 가이드 5편</a></nav><p class="blog-disclosure">도서 소개는 제공된 최종 내지 PDF의 요약이며, 실무 가이드는 공개 출처 기반 응용 콘텐츠입니다. AI 초안을 활용한 Command Marketing 편집 글로 저자의 직접 집필이 아닙니다.</p></header>
<section class="blog-group" id="book-series" aria-labelledby="series-title"><p class="eyebrow">Book notes / 01 — 03</p><h2 class="extra-title" id="series-title">『AI Agent를 지휘하는 마케터』<br>세 편으로 읽는 핵심 구조</h2><p class="section-copy">일을 맡기는 판단, 업무 지시서, 실행과 검수의 루프를 순서대로 소개합니다. 각 글에 도서 페이지 근거를 표시했습니다.</p><div class="blog-cards series-cards">{series_cards}</div></section>
<section class="blog-group" id="practical-guides" aria-labelledby="guides-title"><p class="eyebrow">Practical guides / SEO · GEO · AIEO</p><h2 class="extra-title" id="guides-title">검색과 AI 답변을 위한 실무 가이드</h2><div class="blog-cards">{guide_cards}</div></section>
<div class="article-end"><p class="eyebrow">Read the system</p><h2 class="extra-title">콘텐츠 제작을 반복 가능한 운영으로 바꾸고 싶다면.</h2><p class="section-copy">책의 업무 지시서와 검수·승인 구조를 확인하세요.</p><div class="actions"><a class="button primary" href="/#system">R-G-C-T-O-R 보기</a><a class="button secondary" href="/#diagnosis">내 상황 진단하기</a></div></div></main>{FOOTER}'''
(DIST / 'blog/index.html').write_text(index)

home_cards = ''.join(card(p) for p in ordered)
home_section = f'''<section class="blog-section section" id="blog" data-track-section="blog"><div class="wrap"><div class="blog-head"><div><p class="eyebrow">Book notes / SEO · GEO · AIEO</p><h2 class="section-title">책 소개와 실무 가이드,<br>여덟 편으로 연결합니다.</h2><p class="section-copy">PDF 근거를 명시한 책 소개 시리즈 3편과 공개 출처 기반 SEO·GEO·AIEO 가이드 5편입니다. 도서 요약과 편집 응용의 범위를 구분했습니다.</p></div><a class="text-link" href="/blog">블로그 전체 보기 →</a></div><div class="blog-cards">{home_cards}</div></div></section>'''
LANDING = re.sub(r'<!-- BLOG_SECTION_START -->.*?<!-- BLOG_SECTION_END -->', '<!-- BLOG_SECTION_START -->' + home_section + '<!-- BLOG_SECTION_END -->', LANDING, flags=re.S)
(DIST / 'index.html').write_text(LANDING)
routes = [{'path': '/', 'title': 'AI Agent를 지휘하는 마케터'}, {'path': '/blog', 'title': '도서 소개와 SEO·GEO·AIEO 블로그'}] + [{'path': '/blog/' + p['slug'], 'title': p['title']} for p in POSTS]
(DIST / 'manus-routes.json').write_text(json.dumps({'routes': routes}, ensure_ascii=False, indent=2) + '\n')
ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
root = ET.Element(f'{{{ns}}}urlset')
for route in routes:
    node = ET.SubElement(root, f'{{{ns}}}url')
    ET.SubElement(node, f'{{{ns}}}loc').text = ORIGIN + route['path']
    ET.SubElement(node, f'{{{ns}}}lastmod').text = DATE
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode') + '\n'
for path in (ROOT / 'sitemap.xml', DIST / 'sitemap.xml'):
    path.write_text(sitemap)
llms = re.sub(r'\n## Blog guides\n.*', '', (DIST / 'llms.txt').read_text(), flags=re.S)
llms += '\n## Blog guides\n\n書名: AI Agent를 지휘하는 마케터 · 저자: 박충효. 책 소개 시리즈 3편은 제공 PDF를 요약한 편집 글이며 각 글에 도서 페이지 근거가 있습니다. 원본 PDF는 공개하지 않습니다. 실무 가이드 5편은 공개 출처 기반 응용 콘텐츠로 도서 발췌나 저자의 직접 발언이 아닙니다. AI 초안 활용. AIEO는 사이트 편집상 AI Engine Optimization으로 정의합니다.\n\n- [블로그 목록](' + ORIGIN + '/blog)\n'
llms += '\n'.join(f'- [{p["title"]}]({ORIGIN}/blog/{p["slug"]}): {p["description"]}' for p in ordered) + f'\n\n작성·검토 기준일: {DATE}. llms.txt는 보조 문서이며 검색 노출이나 AI 인용을 보장하지 않습니다.\n'
llms = llms.replace('書名:', '도서명:')
for path in (ROOT / 'llms.txt', DIST / 'llms.txt'):
    path.write_text(llms)
(DIST / '404.html').write_text(head('페이지를 찾을 수 없습니다', '요청한 페이지가 없거나 이동되었습니다. 도서 소개 또는 블로그 목록에서 다시 탐색하세요.', noindex=True) + f'<body class="blog-page">{HEADER}<main class="wrap not-found" id="main"><p class="eyebrow">404 / NOT FOUND</p><h1>이 페이지는 찾을 수 없습니다.</h1><p class="section-copy">도서 소개나 블로그 목록에서 필요한 내용을 다시 찾아보세요.</p><div class="actions"><a class="button primary" href="/">도서 홈</a><a class="button secondary" href="/blog">블로그 목록</a></div></main>{FOOTER}')
print(f'Static blog built: {len(POSTS)} articles ({len(SERIES)} book series), {len(routes)} indexable pages. Origin: {ORIGIN}')
