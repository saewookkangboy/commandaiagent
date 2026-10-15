"""Build static editorial articles and book-introduction series from Markdown.
Production deploys the committed dist directory; Python is an editorial build tool only.
Run: python3 -m pip install -r scripts/requirements.txt && python3 scripts/build_blog.py
"""
from pathlib import Path
from html import escape
from datetime import date
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
PURCHASE_LINK = SOUP.select_one('header.site-head a[data-cta="purchase"]')
assert PURCHASE_LINK and PURCHASE_LINK.get('href'), 'A header purchase link is required.'
PURCHASE_URL = PURCHASE_LINK['href']
FAVICON = str(SOUP.select_one('link[rel="icon"]'))
ANALYTICS_CONFIG = json.loads((ROOT / 'content/analytics-events.json').read_text())
for name, event in ANALYTICS_CONFIG['events'].items():
    assert re.fullmatch(r'[a-z][a-z0-9_]{0,38}', name), name
    assert set(event['parameters']) <= set(ANALYTICS_CONFIG['parameters']), name
(DIST / 'assets/analytics-config.js').write_text('/* Generated from content/analytics-events.json. */\nwindow.commandAnalyticsConfig = Object.freeze(' + json.dumps(ANALYTICS_CONFIG, ensure_ascii=False).replace('<', '\\u003c') + ');\n')
ANALYTICS = '<script src="/assets/analytics-config.js" defer></script><script src="/assets/analytics.js" defer></script>'
BOOK_IMAGE = ORIGIN + '/assets/book-flat.jpg'
SITE = json.loads((ROOT / 'content/site.json').read_text())
POST_MODIFIED = {post['slug']: post.get('modified', post['date']) for post in POSTS}
for post in POSTS:
    assert date.fromisoformat(POST_MODIFIED[post['slug']]) >= date.fromisoformat(post['date']), post['slug']
BLOG_MODIFIED = max(POST_MODIFIED.values())
REVIEWED = max(SITE['llms_reviewed'], SITE['home_modified'], BLOG_MODIFIED)
for value in (SITE['home_modified'], REVIEWED):
    date.fromisoformat(value)
BOOK = {'@type': 'Book', 'name': 'AI Agent를 지휘하는 마케터', 'author': {'@type': 'Person', 'name': '박충효'}, 'url': ORIGIN + '/'}
GUIDE_DISCLOSURE = 'Command Marketing 편집 콘텐츠 · AI 초안 활용, 공개 출처 기반 편집. 도서 발췌나 저자의 직접 발언이 아닌 실무 응용 콘텐츠입니다. 예시는 실제 캠페인 성과가 아니며 검색 노출과 AI 인용을 보장하지 않습니다.'
SERIES_DISCLOSURE = 'Command Marketing 도서 소개 · AI 초안 활용. 제공된 최종 내지 PDF를 근거로 요약·소개한 편집 콘텐츠이며 저자가 직접 집필한 블로그 글은 아닙니다. 별도 표시한 예시는 편집 응용입니다. 원본 PDF는 공개하지 않습니다.'


def graph_json(data):
    return json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')


def post_keywords(post):
    """Editorial topic labels, not a Google ranking mechanism."""
    return list(dict.fromkeys([post['primary_keyword'], *post['secondary_keywords']]))


def head(title, description, path=None, graph=None, post=None, noindex=False, article_ux=False):
    url = ORIGIN + path if path is not None else None
    canonical = f'<link rel="canonical" href="{escape(url, quote=True)}">' if url else ''
    og_url = f'<meta property="og:url" content="{escape(url, quote=True)}">' if url else ''
    image = ORIGIN + post['image_jpg'] if post else BOOK_IMAGE
    image_alt = post['image_alt'] if post else 'AI Agent를 지휘하는 마케터 도서 이미지'
    image_dimensions = '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="675">' if post else ''
    dates = ''
    topic_meta = ''
    if post:
        dates = f'<meta property="article:published_time" content="{post["date"]}T00:00:00+09:00"><meta property="article:modified_time" content="{post.get("modified", post["date"])}T00:00:00+09:00">'
        # Kept as descriptive metadata only: Google ignores meta keywords.
        keywords = post_keywords(post)
        topic_meta = f'<meta name="keywords" content="{escape(", ".join(keywords), quote=True)}">\n'
        topic_meta += f'<meta property="article:section" content="{escape(post["category"], quote=True)}">\n'
        topic_meta += '\n'.join(f'<meta property="article:tag" content="{escape(keyword, quote=True)}">' for keyword in keywords)
    schema = f'<script type="application/ld+json">{graph_json(graph)}</script>' if graph else ''
    article_assets = '<link rel="stylesheet" href="/assets/article-ux.css"><script src="/assets/article-ux.js" defer></script>' if article_ux else ''
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
	{dates}{topic_meta}{FAVICON}<link rel="stylesheet" href="/assets/site.css"><link rel="stylesheet" href="/assets/enhancements.css">{article_assets}
<link rel="sitemap" type="application/xml" href="/sitemap.xml"><link rel="describedby" href="/llms.txt">
{ANALYTICS}{schema}</head>'''


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
    previous = f'<a href="/blog/{SERIES[index-1]["slug"]}" aria-label="이전 편: {escape(SERIES[index-1]["short_title"], quote=True)}">← 이전 편</a>' if index else ''
    following = f'<a href="/blog/{SERIES[index+1]["slug"]}" aria-label="다음 편: {escape(SERIES[index+1]["short_title"], quote=True)}">다음 편 →</a>' if index + 1 < len(SERIES) else '<a href="/#contents">책 전체 구성 보기 →</a>'
    return f'''<nav class="series-nav" aria-label="책 소개 시리즈"><p class="series-status">책 소개 시리즈 · 현재 {post["series_order"]}/{len(SERIES)}</p><div class="series-pager">{previous}{following}</div>
<details class="series-full-list"><summary>시리즈 전체 {len(SERIES)}편 보기</summary><ol>{entries}</ol></details></nav>'''


WORK_BY_SLUG = {
    'seo-geo-aieo-guide': 'content',
    'geo-content-structure': 'content',
    'technical-seo-ai-search': 'review',
    'rgctor-content-workflow': 'review',
    'ai-search-measurement': 'performance',
    'marketer-ai-agent-workflow-design': 'review',
    'why-marketers-need-ai-agents': 'review',
}


def consulting_href(post, location='direct'):
    work = WORK_BY_SLUG.get(post['slug'], 'undecided')
    intent = 'education' if post.get('kind') == 'book-series' else 'workflow'
    return f'/consulting?from={post["slug"]}&work={work}&intent={intent}&cta={location}-team'


def cta_primary(post, location, class_name='button primary'):
    position = f'article-{location}' if location != 'mobile' else 'mobile-sticky'
    cta_type = 'book' if post.get('kind') == 'book-series' else 'team'
    cta_id = f'{location}-{cta_type}'
    if cta_type == 'book':
        return f'<a class="{class_name}" href="{escape(PURCHASE_URL, quote=True)}" target="_blank" rel="noreferrer" data-cta="purchase" data-position="{position}" data-cta-id="{cta_id}">교보문고에서 책 구매</a>'
    return f'<a class="{class_name}" href="{escape(consulting_href(post, location), quote=True)}" data-consulting-path data-position="{position}" data-cta-id="{cta_id}">팀 검수·운영 체계 문의</a>'


def article_cta(post, location):
    position = f'article-{location}'
    primary = cta_primary(post, location)
    if post.get('kind') == 'book-series':
        heading = '책의 전체 구성을 확인하고, 적용 범위를 정하세요.'
        copy = '도서의 전체 구성과 구매 경로를 확인한 뒤, 조직 적용은 별도 문의에서 현재 업무 범위에 맞춰 살펴볼 수 있습니다.'
        context_link = '<a class="article-cta-context-link" href="/#contents">책 전체 구성 보기 →</a>'
        secondary = f'<a class="button secondary" href="{escape(consulting_href(post, location), quote=True)}" data-consulting-path data-position="{position}" data-cta-id="{location}-team">팀 적용 범위 문의</a>'
    else:
        heading = '글의 기준을 팀 검수와 운영 흐름에 연결하세요.'
        copy = f'{escape(post["primary_keyword"])} 내용을 바탕으로, 콘텐츠 검수와 운영 기준을 팀의 현재 업무에 맞춰 확인해 보세요.'
        resource_path = '/resources/rgctor-worksheet' if post['slug'] in ('rgctor-content-workflow', 'marketer-ai-agent-workflow-design', 'why-marketers-need-ai-agents') else '/resources/content-search-checklist'
        resource_label = 'R-G-C-T-O-R 업무 지시서 워크시트 보기' if resource_path.endswith('rgctor-worksheet') else '콘텐츠·검색 점검표 보기'
        context_link = ''
        resource_id = resource_path.rsplit('/', 1)[-1]
        secondary = f'<a class="button secondary" href="{resource_path}" data-resource-id="{resource_id}" data-cta-id="{location}-resource" data-position="{position}">{resource_label}</a>'
    label = '실행 기준 이어 보기' if location == 'inline' else '다음 단계'
    return f'''<section class="article-cta article-cta-{location}"{' id="article-end"' if location == 'end' else ''} aria-label="{label}">
<p class="eyebrow">{label}</p><h3>{heading}</h3><p>{copy}</p>{context_link}<div class="article-cta-actions">{primary}{secondary}</div></section>'''


def mobile_cta(post):
    return f'''<aside class="article-mobile-cta" aria-label="빠른 다음 행동" hidden>
{cta_primary(post, 'mobile', 'article-mobile-cta-link button primary')}<button class="article-mobile-cta-close" type="button" aria-label="빠른 다음 행동 닫기">×</button></aside>'''


def insert_inline_cta(rendered, cta_markup):
    """Place one CTA after the first practical example or execution-check section."""
    useful = re.compile(r'예시|실행\s*체크|체크리스트|점검표')
    headings = rendered.find_all('h2')
    anchor = next((heading for heading in headings if useful.search(heading.get_text(' ', strip=True))), None)
    cta = BeautifulSoup(cta_markup, 'html.parser').find('section')
    assert cta, 'Inline CTA markup must contain one section.'
    if anchor:
        following = anchor.find_next_sibling('h2')
        if following:
            following.insert_before(cta)
        else:
            rendered.append(cta)
    else:
        rendered.append(cta)


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
    article['alternativeHeadline'] = post['seo_title']
    article['abstract'] = post['search_summary']
    article['keywords'] = post_keywords(post)
    article['about'] = [{'@type': 'Thing', 'name': keyword} for keyword in post_keywords(post)]
    is_series = post.get('kind') == 'book-series'
    if is_series:
        article['isBasedOn'] = BOOK
        article['citation'].append(BOOK)
    graph = {'@context': 'https://schema.org', '@graph': [article, breadcrumb_graph(post)]}
    related = ''.join(card(BY_SLUG[slug]) for slug in post['related'])
    disclosure = SERIES_DISCLOSURE if is_series else GUIDE_DISCLOSURE
    date_text = f'게시: <time datetime="{post["date"]}">{post["date"]}</time> · 검토·수정: <time datetime="{post.get("modified", post["date"])}">{post.get("modified", post["date"])}</time>'
    topics = post_keywords(post)
    topic_labels = ''.join(f'<li>{escape(keyword)}</li>' for keyword in topics[:3])
    remaining_topics = ''.join(f'<li>{escape(keyword)}</li>' for keyword in topics[3:])
    topic_more = f'<details class="article-topic-details"><summary>주제 {len(topics) - 3}개 더 보기</summary><ul class="article-topics" aria-label="추가 핵심 주제">{remaining_topics}</ul></details>' if remaining_topics else ''
    disclosure_short = 'Command Marketing 편집 · AI 초안 활용 · ' + ('제공된 최종 내지 PDF를 근거로 한 도서 요약' if is_series else '공개 출처 기반 실무 응용 · 도서 요약 아님')
    insert_inline_cta(rendered, article_cta(post, 'inline'))
    html = head(post['seo_title'], post['description'], path, graph, post=post, article_ux=True) + f'''
<body class="blog-page" data-page-type="blog_article" data-ui-variant="ux-v1" data-content-group="{'book_series' if is_series else 'practical_guide'}" data-series-order="{post.get('series_order', '')}" data-article="{post['slug']}"><a class="skip-link" href="#main">본문으로 이동</a>{HEADER}
<main class="blog-main wrap" id="main">{breadcrumbs(post)}
<header class="blog-heading article-head"><div class="article-head-copy"><p class="eyebrow">{escape(post['category'])}</p><h1>{escape(post['title'])}</h1>
<p class="article-meta"><span>검토: <time datetime="{post.get('modified', post['date'])}">{post.get('modified', post['date'])}</time></span><span>약 {reading}분 읽기</span></p></div>
<figure class="article-head-visual">{picture(post, hero=True)}<figcaption>AI 생성 카툰 · 손글씨</figcaption></figure>
<div class="article-head-details"><p class="article-summary">{escape(post['search_summary'])}</p><ul class="article-topics" aria-label="이 글의 핵심 주제">{topic_labels}</ul>{topic_more}
<p class="article-disclosure-short">{disclosure_short}</p><details class="article-disclosure-details"><summary>편집·출처 고지 자세히</summary><p>{disclosure}</p><p>{date_text}</p></details></div></header>
{series_navigation(post)}
<div class="article-layout"><aside class="article-toc" aria-label="글 목차"><nav class="article-toc-desktop" aria-label="이 글의 순서"><p>이 글의 순서</p><ol>{''.join(toc)}</ol></nav>
<details class="article-toc-mobile"><summary>이 글의 순서</summary><ol>{''.join(toc)}</ol></details></aside>
<article class="article-body" aria-label="{escape(post['title'], quote=True)}">{str(rendered)}{article_cta(post, 'end')}</article></div>
{mobile_cta(post)}
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
index = head('AI 마케팅 책 소개와 SEO·GEO·AIEO 실무 블로그', f'AI Agent를 지휘하는 마케터 책 소개 시리즈 {len(SERIES)}편과 SEO·GEO·AIEO 실무 가이드 {len(GUIDES)}편. Agent 워크플로우 설계, 거버넌스, 업무 지시서부터 기술 SEO와 AI 검색 성과 측정까지 읽어 보세요.', '/blog', graph) + f'''
<body class="blog-page" data-page-type="blog_index" data-content-group="blog_index"><a class="skip-link" href="#main">본문으로 이동</a>{HEADER}<main class="blog-main wrap" id="main">{breadcrumbs()}
<header class="blog-heading"><p class="eyebrow">Command Marketing / Field notes</p><h1>책에서 운영으로,<br>검색에서 답변으로.</h1><p class="section-copy">책 소개 시리즈 {len(SERIES)}편으로 AI 마케팅의 운영 구조를 읽고, 실무 가이드 {len(GUIDES)}편으로 Agent 설계·검색·콘텐츠·검수·측정의 기준을 세우세요.</p><nav class="blog-category-nav" aria-label="블로그 콘텐츠 분류"><a href="#book-series">책 소개 시리즈 {len(SERIES)}편</a><a href="#practical-guides">SEO·GEO·AIEO 가이드 {len(GUIDES)}편</a></nav><p class="blog-disclosure">도서 소개는 제공된 최종 내지 PDF의 요약이며, 실무 가이드는 공개 출처 기반 응용 콘텐츠입니다. AI 초안을 활용한 Command Marketing 편집 글로 저자의 직접 집필이 아닙니다.</p></header>
<section class="blog-group" id="book-series" aria-labelledby="series-title"><p class="eyebrow">Book notes / 01 — 03</p><h2 class="extra-title" id="series-title">『AI Agent를 지휘하는 마케터』<br>세 편으로 읽는 핵심 구조</h2><p class="section-copy">일을 맡기는 판단, 업무 지시서, 실행과 검수의 루프를 순서대로 소개합니다. 각 글에 도서 페이지 근거를 표시했습니다.</p><div class="blog-cards series-cards">{series_cards}</div></section>
<section class="blog-group" id="practical-guides" aria-labelledby="guides-title"><p class="eyebrow">Practical guides / SEO · GEO · AIEO</p><h2 class="extra-title" id="guides-title">검색과 AI 답변을 위한 실무 가이드</h2><div class="blog-cards">{guide_cards}</div></section>
<div class="article-end"><p class="eyebrow">Read the system</p><h2 class="extra-title">콘텐츠 제작을 반복 가능한 운영으로 바꾸고 싶다면.</h2><p class="section-copy">책의 업무 지시서와 검수·승인 구조를 확인하세요.</p><div class="actions"><a class="button primary" href="/#system">R-G-C-T-O-R 보기</a><a class="button secondary" href="/#diagnosis">내 상황 진단하기</a></div></div></main>{FOOTER}'''
(DIST / 'blog/index.html').write_text(index)

home_cards = ''.join(card(p) for p in ordered)
home_section = f'''<section class="blog-section section" id="blog" data-track-section="blog"><div class="wrap"><div class="blog-head"><div><p class="eyebrow">Book notes / SEO · GEO · AIEO</p><h2 class="section-title">책 소개와 실무 가이드,<br>{len(POSTS)}편으로 연결합니다.</h2><p class="section-copy">PDF 근거를 명시한 책 소개 시리즈 {len(SERIES)}편과 공개 출처 기반 SEO·GEO·AIEO 가이드 {len(GUIDES)}편입니다. Agent 워크플로우 설계부터 검색과 콘텐츠 운영까지, 도서 요약과 편집 응용의 범위를 구분했습니다.</p></div><a class="text-link" href="/blog">블로그 전체 보기 →</a></div><div class="blog-cards">{home_cards}</div></div></section>'''
LANDING = re.sub(r'<!-- BLOG_SECTION_START -->.*?<!-- BLOG_SECTION_END -->', '<!-- BLOG_SECTION_START -->' + home_section + '<!-- BLOG_SECTION_END -->', LANDING, flags=re.S)
(DIST / 'index.html').write_text(LANDING)

# build_funnel owns the static consulting/resources pages and returns their route metadata.
# It is imported only after this module's reusable head, header, footer and site data exist.
from build_funnel import build_funnel

funnel_routes = build_funnel(DIST, head, HEADER, FOOTER, ORIGIN, SITE)
REVIEWED = max(REVIEWED, *(route['lastmod'] for route in funnel_routes))
assert isinstance(funnel_routes, list), 'build_funnel must return a list of route metadata.'
for route in funnel_routes:
    assert isinstance(route, dict), 'A funnel route must be a dictionary.'
    assert isinstance(route.get('path'), str) and route['path'].startswith('/'), route
    assert isinstance(route.get('title'), str) and route['title'], route
    assert isinstance(route.get('lastmod'), str), route
    date.fromisoformat(route['lastmod'])
    assert 'noindex' not in route or isinstance(route['noindex'], bool), route

base_routes = [{'path': '/', 'title': 'AI Agent를 지휘하는 마케터'}, {'path': '/blog', 'title': '도서 소개와 SEO·GEO·AIEO 블로그'}] + [{'path': '/blog/' + p['slug'], 'title': p['title']} for p in POSTS]
routes = base_routes + funnel_routes
assert len({route['path'] for route in routes}) == len(routes), 'Duplicate static route paths are not allowed.'
indexable_routes = [route for route in routes if not route.get('noindex', False)]
manifest_routes = [{'path': route['path'], 'title': route['title']} for route in routes]
(DIST / 'manus-routes.json').write_text(json.dumps({'routes': manifest_routes}, ensure_ascii=False, indent=2) + '\n')
ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
image_ns = 'http://www.google.com/schemas/sitemap-image/1.1'
ET.register_namespace('image', image_ns)
route_modified = {'/': SITE['home_modified'], '/blog': BLOG_MODIFIED}
route_images = {'/': BOOK_IMAGE}
for post in POSTS:
    route_modified['/blog/' + post['slug']] = POST_MODIFIED[post['slug']]
    route_images['/blog/' + post['slug']] = ORIGIN + post['image_jpg']
for route in funnel_routes:
    route_modified[route['path']] = route['lastmod']
root = ET.Element(f'{{{ns}}}urlset')
for route in indexable_routes:
    node = ET.SubElement(root, f'{{{ns}}}url')
    ET.SubElement(node, f'{{{ns}}}loc').text = ORIGIN + route['path']
    ET.SubElement(node, f'{{{ns}}}lastmod').text = route_modified[route['path']]
    if route['path'] in route_images:
        image = ET.SubElement(node, f'{{{image_ns}}}image')
        ET.SubElement(image, f'{{{image_ns}}}loc').text = route_images[route['path']]
ET.indent(root, space='  ')
sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode') + '\n'
for path in (ROOT / 'sitemap.xml', DIST / 'sitemap.xml'):
    path.write_text(sitemap)
llms = (ROOT / 'content/llms-base.md').read_text().rstrip() + '\n'
for title, group in ((f'도서 소개 시리즈 {len(SERIES)}편', SERIES), (f'SEO·GEO·AIEO 실무 가이드 {len(GUIDES)}편', GUIDES)):
    llms += '\n## ' + title + '\n\n'
    llms += '\n'.join(f'- [{post["seo_title"]}]({ORIGIN}/blog/{post["slug"]}): {post["search_summary"]}' for post in group) + '\n'
llms += f'\n## 공개 편집 자료와 팀 적용 문의\n\n- [R-G-C-T-O-R 업무 지시서 워크시트]({ORIGIN}/resources/rgctor-worksheet): 공개 편집 응용 자료이며 도서 원본 PDF가 아닙니다.\n- [콘텐츠·검색 점검표]({ORIGIN}/resources/content-search-checklist): 공개 편집 응용 자료이며 도서 원본 PDF가 아닙니다.\n- [팀 적용 문의]({ORIGIN}/consulting): 콘텐츠 검수·운영 체계의 적용 범위를 문의하는 경로입니다.\n'
llms += f'\n## 검색 보조 문서\n\n- [XML 사이트맵]({ORIGIN}/sitemap.xml): 현재 색인 대상 정규 URL {len(indexable_routes)}개와 대표 이미지\n- [크롤러 접근 정책]({ORIGIN}/robots.txt): 검색·사용자 요청 크롤러와 모델 학습 크롤러의 정책 구분\n'
llms += f'\n문서 검토 기준일: {REVIEWED}. 각 페이지의 최종 콘텐츠 수정일은 사이트맵과 글의 게시·검토 표시를 참고하세요. llms.txt는 보조 문서이며 검색 노출이나 AI 인용을 보장하지 않습니다.\n'
for path in (ROOT / 'llms.txt', DIST / 'llms.txt'):
    path.write_text(llms)
(DIST / '404.html').write_text(head('페이지를 찾을 수 없습니다', '요청한 페이지가 없거나 이동되었습니다. 도서 소개 또는 블로그 목록에서 다시 탐색하세요.', noindex=True) + f'<body class="blog-page">{HEADER}<main class="wrap not-found" id="main"><p class="eyebrow">404 / NOT FOUND</p><h1>이 페이지는 찾을 수 없습니다.</h1><p class="section-copy">도서 소개나 블로그 목록에서 필요한 내용을 다시 찾아보세요.</p><div class="actions"><a class="button primary" href="/">도서 홈</a><a class="button secondary" href="/blog">블로그 목록</a></div></main>{FOOTER}')
print(f'Static blog built: {len(POSTS)} articles ({len(SERIES)} book series), {len(indexable_routes)} indexable pages. Origin: {ORIGIN}')
