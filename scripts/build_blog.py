"""Build the editorial blog as static HTML. Production still deploys dist directly.
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
LANDING = (DIST / 'index.html').read_text()
SOUP = BeautifulSoup(LANDING, 'html.parser')
STYLE = DIST / 'assets/site.css'
# Copy the original design system once; do not overwrite an independently edited style.
if not STYLE.exists():
    STYLE.write_text(SOUP.style.string.strip() + '\n')
HEADER = str(SOUP.select_one('header.site-head'))
HEADER = re.sub(r'href="#', 'href="/#', HEADER)
FAVICON = str(SOUP.select_one('link[rel="icon"]'))
TRACKING = str(SOUP.find('script'))
PIXEL = next(str(tag) for tag in SOUP.find_all('script') if "fbq('init'" in (tag.string or ''))
BOOK_IMAGE = ORIGIN + '/assets/book-flat.jpg'
DATE = '2026-10-14'


def graph_json(data):
    return json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')


def head(title, description, path=None, graph=None, article=False, noindex=False):
    url = ORIGIN + path if path is not None else None
    canonical = f'<link rel="canonical" href="{escape(url, quote=True)}">' if url else ''
    og_url = f'<meta property="og:url" content="{escape(url, quote=True)}">' if url else ''
    dates = f'<meta property="article:published_time" content="{DATE}T00:00:00+09:00"><meta property="article:modified_time" content="{DATE}T00:00:00+09:00">' if article else ''
    schema = f'<script type="application/ld+json">{graph_json(graph)}</script>' if graph else ''
    return f'''<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} | Command Marketing</title>
<meta name="description" content="{escape(description, quote=True)}">
<meta name="author" content="Command Marketing"><meta name="publisher" content="TROE">
<meta name="robots" content="{'noindex,follow' if noindex else 'index,follow,max-snippet:-1,max-image-preview:large'}">
<meta name="referrer" content="strict-origin-when-cross-origin"><meta name="theme-color" content="#eef3f1">
{canonical}<meta property="og:locale" content="ko_KR"><meta property="og:type" content="{'article' if article else 'website'}">
<meta property="og:site_name" content="Command Marketing"><meta property="og:title" content="{escape(title, quote=True)}">
<meta property="og:description" content="{escape(description, quote=True)}">{og_url}
<meta property="og:image" content="{BOOK_IMAGE}"><meta property="og:image:alt" content="AI Agent를 지휘하는 마케터 도서 이미지">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(title, quote=True)}">
<meta name="twitter:description" content="{escape(description, quote=True)}"><meta name="twitter:image" content="{BOOK_IMAGE}">
{dates}{FAVICON}<link rel="stylesheet" href="/assets/site.css"><link rel="stylesheet" href="/assets/enhancements.css">
<link rel="sitemap" type="application/xml" href="/sitemap.xml"><link rel="describedby" href="/llms.txt">
{TRACKING}{PIXEL}{schema}</head>'''


def breadcrumbs(post=None):
    last = '<span aria-current="page">블로그</span>' if not post else f'<a href="/blog">블로그</a><span aria-hidden="true">/</span><span aria-current="page">{escape(post["category"])}</span>'
    return f'<nav class="breadcrumbs" aria-label="현재 위치"><a href="/">도서 홈</a><span aria-hidden="true">/</span>{last}</nav>'


def breadcrumb_graph(post=None):
    rows = [{'@type': 'ListItem', 'position': 1, 'name': '도서 홈', 'item': ORIGIN + '/'}, {'@type': 'ListItem', 'position': 2, 'name': '블로그', 'item': ORIGIN + '/blog'}]
    if post:
        rows.append({'@type': 'ListItem', 'position': 3, 'name': post['category'], 'item': ORIGIN + '/blog/' + post['slug']})
    return {'@type': 'BreadcrumbList', 'itemListElement': rows}


def card(post):
    href = '/blog/' + post['slug']
    return f'''<article class="blog-card"><p class="eyebrow">{escape(post['category'])} / {post['date']}</p>
<h3><a href="{href}" data-blog-link="{post['slug']}">{escape(post['title'])}</a></h3>
<p>{escape(post['description'])}</p><a class="text-link" href="{href}" data-blog-link="{post['slug']}">가이드 읽기 →</a></article>'''


FOOTER = '''<footer class="blog-footer"><div class="wrap"><a class="text-link" href="/">AI Agent를 지휘하는 마케터</a> · <a href="/blog">블로그</a> · <a href="https://troe.kr/">TROE</a><br>© 2026 TROE. ALL RIGHTS RESERVED.</div></footer><script src="/assets/enhancements.js" defer></script></body></html>'''
DISCLOSURE = 'Command Marketing 편집 콘텐츠 · AI 초안 활용, 공개 출처 기반 편집. 도서 발췌나 저자의 직접 발언이 아닌 실무 응용 콘텐츠입니다. 예시는 실제 캠페인 성과가 아니며 검색 노출과 AI 인용을 보장하지 않습니다.'


for post in POSTS:
    src = (ROOT / 'content/blog' / (post['slug'] + '.md')).read_text()
    first = src.splitlines()[0].removeprefix('# ').strip()
    assert first == post['title'], post['slug']
    # Retain shortcut-reference definitions, then add a visible source bibliography.
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
    graph = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'BlogPosting', '@id': url + '#article', 'mainEntityOfPage': url, 'url': url,
         'headline': post['title'], 'description': post['description'], 'datePublished': post['date'], 'dateModified': post['date'],
         'inLanguage': 'ko-KR', 'image': BOOK_IMAGE, 'articleSection': post['category'],
         'author': {'@type': 'Organization', 'name': 'Command Marketing', 'url': ORIGIN + '/blog'},
         'publisher': {'@type': 'Organization', 'name': 'TROE', 'url': 'https://troe.kr/'},
         'isPartOf': {'@type': 'Blog', '@id': ORIGIN + '/blog#blog', 'name': 'Command Marketing 블로그'},
         'citation': [url for _, url, _ in refs]},
        breadcrumb_graph(post)
    ]}
    related = ''.join(card(BY_SLUG[slug]) for slug in post['related'])
    html = head(post['title'], post['description'], path, graph, article=True) + f'''
<body class="blog-page" data-article="{post['slug']}"><a class="skip-link" href="#main">본문으로 이동</a>{HEADER}
<main class="blog-main wrap" id="main">{breadcrumbs(post)}
<header class="blog-heading"><p class="eyebrow">{escape(post['category'])}</p><h1>{escape(post['title'])}</h1>
<p class="article-meta"><span>편집: Command Marketing</span><span>작성·수정: <time datetime="{post['date']}">{post['date']}</time></span><span>약 {reading}분 읽기</span></p>
<p class="blog-disclosure">{DISCLOSURE}</p></header>
<div class="article-layout"><aside class="article-toc" aria-label="글 목차"><p>이 글의 순서</p><ol>{''.join(toc)}</ol></aside>
<article class="article-body" aria-label="{escape(post['title'], quote=True)}">{str(rendered)}
<div class="article-end" id="article-end"><h2>도구보다 운영 기준을 먼저 세우세요.</h2><p>책의 R-G-C-T-O-R 구조와 3주 훈련을 확인하거나 팀에 적용할 범위를 살펴보세요.</p>
<div class="actions"><a class="button primary" href="/#contents">책 구성 보기</a><a class="button secondary" href="/#consulting" data-consulting-path data-position="blog-article">팀 적용 범위 보기</a></div></div></article></div>
<section class="blog-section" style="padding:40px 0 70px" aria-labelledby="related-title"><h2 class="extra-title" id="related-title">함께 읽으면 좋은 가이드</h2><div class="blog-cards">{related}</div><a class="text-link" href="/blog">블로그 전체 보기 →</a></section></main>{FOOTER}'''
    directory = DIST / 'blog' / post['slug']
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'index.html').write_text(html)

cards = ''.join(card(post) for post in POSTS)
items = [{'@type': 'ListItem', 'position': i + 1, 'url': ORIGIN + '/blog/' + post['slug'], 'name': post['title']} for i, post in enumerate(POSTS)]
graph = {'@context': 'https://schema.org', '@graph': [
    {'@type': 'CollectionPage', '@id': ORIGIN + '/blog#webpage', 'url': ORIGIN + '/blog', 'name': 'SEO·GEO·AIEO 실무 블로그', 'inLanguage': 'ko-KR', 'mainEntity': {'@type': 'ItemList', 'itemListElement': items}},
    {'@type': 'Blog', '@id': ORIGIN + '/blog#blog', 'url': ORIGIN + '/blog', 'name': 'Command Marketing 블로그', 'inLanguage': 'ko-KR', 'publisher': {'@type': 'Organization', 'name': 'TROE', 'url': 'https://troe.kr/'}},
    breadcrumb_graph()
]}
index = head('SEO·GEO·AIEO 실무 블로그', 'AI 검색 시대의 콘텐츠 전략부터 기술 SEO, 출처 검수, 콘텐츠 Agent 운영, 성과 측정까지. 마케터와 팀 리더가 바로 적용할 수 있는 다섯 가지 가이드를 확인하세요.', '/blog', graph) + f'''
<body class="blog-page"><a class="skip-link" href="#main">본문으로 이동</a>{HEADER}<main class="blog-main wrap" id="main">{breadcrumbs()}
<header class="blog-heading"><p class="eyebrow">Command Marketing / Field notes</p><h1>검색에 발견되고,<br>답변의 근거가 되는 콘텐츠.</h1><p class="section-copy">SEO·GEO·AIEO를 새로운 비법이 아니라, 질문에 답하고 근거를 검수하는 운영 관점으로 다룹니다. 전략·콘텐츠·기술·Agent·측정의 다섯 가이드를 읽어 보세요.</p><p class="blog-disclosure">{DISCLOSURE}</p></header>
<div class="blog-cards">{cards}</div><div class="article-end"><p class="eyebrow">Read the system</p><h2 class="extra-title">콘텐츠 제작을 반복 가능한 운영으로 바꾸고 싶다면.</h2><p class="section-copy">『AI Agent를 지휘하는 마케터』의 업무 지시서와 검수·승인 구조를 확인하세요.</p><div class="actions"><a class="button primary" href="/#system">R-G-C-T-O-R 보기</a><a class="button secondary" href="/#diagnosis">내 상황 진단하기</a></div></div></main>{FOOTER}'''
(DIST / 'blog/index.html').write_text(index)

home_section = f'''<section class="blog-section section" id="blog" data-track-section="blog"><div class="wrap"><div class="blog-head"><div><p class="eyebrow">Field notes / SEO · GEO · AIEO</p><h2 class="section-title">검색과 AI 답변을 위한 콘텐츠 운영 가이드.</h2><p class="section-copy">정의부터 실무 설계와 측정까지, 다섯 편으로 연결합니다. 도서 발췌가 아닌 공개 출처 기반의 편집 콘텐츠입니다.</p></div><a class="text-link" href="/blog">블로그 전체 보기 →</a></div><div class="blog-cards">{cards}</div></div></section>'''
if '<!-- BLOG_SECTION -->' in LANDING:
    LANDING = LANDING.replace('<!-- BLOG_SECTION -->', '<!-- BLOG_SECTION_START -->' + home_section + '<!-- BLOG_SECTION_END -->')
else:
    LANDING = re.sub(r'<!-- BLOG_SECTION_START -->.*?<!-- BLOG_SECTION_END -->', '<!-- BLOG_SECTION_START -->' + home_section + '<!-- BLOG_SECTION_END -->', LANDING, flags=re.S)
(DIST / 'index.html').write_text(LANDING)

routes = [{'path': '/', 'title': 'AI Agent를 지휘하는 마케터'}, {'path': '/blog', 'title': 'SEO·GEO·AIEO 실무 블로그'}] + [{'path': '/blog/' + post['slug'], 'title': post['title']} for post in POSTS]
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
llms = (DIST / 'llms.txt').read_text()
llms = re.sub(r'\n## Blog guides\n.*', '', llms, flags=re.S)
llms = llms.replace('출판·브랜드 운영 주체', '브랜드·교육·컨설팅 안내').replace('https://book.allrounder.im/#preview): Role', 'https://book.allrounder.im/#system): Role')
llms += '\n## Blog guides\n\nSEO·GEO·AIEO 실무 응용을 다룬 사이트 편집 콘텐츠입니다. 도서 원문이나 저자의 직접 발언이 아닙니다. AIEO는 이 사이트에서 AI Engine Optimization이라는 편집상 용어로 정의합니다.\n\n- [블로그 목록](' + ORIGIN + '/blog)\n'
llms += '\n'.join(f'- [{post["title"]}]({ORIGIN}/blog/{post["slug"]}): {post["description"]}' for post in POSTS) + '\n\n작성·수정 기준일: 2026-10-14. llms.txt는 보조 문서이며 검색 노출이나 AI 인용을 보장하지 않습니다.\n'
for path in (ROOT / 'llms.txt', DIST / 'llms.txt'):
    path.write_text(llms)
(DIST / '404.html').write_text(head('페이지를 찾을 수 없습니다', '요청한 페이지가 없거나 이동되었습니다. 도서 소개 또는 블로그 목록에서 다시 탐색하세요.', noindex=True) + f'<body class="blog-page">{HEADER}<main class="wrap not-found" id="main"><p class="eyebrow">404 / NOT FOUND</p><h1>이 페이지는 찾을 수 없습니다.</h1><p class="section-copy">도서 소개나 블로그 목록에서 필요한 내용을 다시 찾아보세요.</p><div class="actions"><a class="button primary" href="/">도서 홈</a><a class="button secondary" href="/blog">블로그 목록</a></div></main>{FOOTER}')
print(f'Static blog built: {len(POSTS)} articles, {len(routes)} indexable pages. Origin: {ORIGIN}')
