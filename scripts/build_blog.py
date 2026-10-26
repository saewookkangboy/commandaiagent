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
from article_cta import insert_inline_cta, validate_cta_layout
from blog_sections import load_sections

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
ORIGIN = 'https://book.allrounder.im'
POSTS = json.loads((ROOT / 'content/blog/posts.json').read_text())
BY_SLUG = {post['slug']: post for post in POSTS}
SERIES = sorted([p for p in POSTS if p.get('kind') == 'book-series'], key=lambda p: p['series_order'])
SCHEDULED_SERIES_FILE = ROOT / 'content/scheduled/command-marketing-os/posts.json'
COMMAND_SERIES = json.loads(SCHEDULED_SERIES_FILE.read_text()) if SCHEDULED_SERIES_FILE.exists() else []
GUIDES = [p for p in POSTS if p.get('kind') != 'book-series']
TOPIC_SECTIONS = load_sections(ROOT / 'content/blog/sections.json', POSTS)
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
HOME_DESCRIPTION = SITE['home_description']
assert HOME_DESCRIPTION == HOME_DESCRIPTION.strip() and 1 <= len(HOME_DESCRIPTION) <= 80, 'Home description must meet the supplied Naver URL-inspection recommendation.'
for attribute, name in (('name', 'description'), ('property', 'og:description'), ('name', 'twitter:description')):
    pattern = rf'(<meta\s+{attribute}="{re.escape(name)}"\s+content=")[^"]*("\s*/?>)'
    LANDING, count = re.subn(pattern, lambda match: match[1] + escape(HOME_DESCRIPTION, quote=True) + match[2], LANDING)
    assert count == 1, f'Home {name} metadata is missing or duplicated.'
POST_MODIFIED = {post['slug']: post.get('modified', post['date']) for post in POSTS}
for post in POSTS:
    assert date.fromisoformat(POST_MODIFIED[post['slug']]) >= date.fromisoformat(post['date']), post['slug']
BLOG_MODIFIED = max(SITE.get('blog_modified', '0001-01-01'), *POST_MODIFIED.values())
REVIEWED = max(SITE['llms_reviewed'], SITE['home_modified'], BLOG_MODIFIED)
for value in (SITE['home_modified'], REVIEWED):
    date.fromisoformat(value)
BOOK = {'@type': 'Book', 'name': 'AI Agent를 지휘하는 마케터', 'author': {'@type': 'Person', 'name': '박충효'}, 'url': ORIGIN + '/'}
GUIDE_DISCLOSURE = 'Command Marketing 편집 콘텐츠 · AI 초안 활용, 공개 출처 기반 편집. 도서 발췌나 저자의 직접 발언이 아닌 실무 응용 콘텐츠입니다. 예시는 실제 캠페인 성과가 아니며 검색 노출과 AI 인용을 보장하지 않습니다.'
SERIES_DISCLOSURE = 'Command Marketing 도서 소개 · AI 초안 활용. 『AI Agent를 지휘하는 마케터』의 주제와 구성을 소개한 편집 콘텐츠이며 저자가 직접 집필한 블로그 글은 아닙니다. 별도 표시한 예시는 편집 응용입니다. 이 글은 도서 전체를 대체하지 않습니다.'
BOOK_BASED_GUIDE_DISCLOSURE = 'Command Marketing 실무 응용 · AI 초안 활용. 도서의 일반 주제와 공개 출처를 바탕으로 구성한 편집 콘텐츠이며 저자가 직접 집필한 글은 아닙니다. 가상 B2B 캠페인·복사형 지시서·점검표는 편집 응용이고, 실제 고객사 성과나 업무 효율·검색 노출·AI 인용·문의·매출을 보장하지 않습니다.'
SERIES_SHORT_DISCLOSURE = 'Command Marketing 도서 소개 · AI 초안 활용 · 도서의 주제와 구성을 소개한 편집 콘텐츠'
BOOK_BASED_GUIDE_SHORT_DISCLOSURE = 'Command Marketing 편집 · AI 초안 활용 · 도서 주제를 바탕으로 한 실무 응용'


def graph_json(data):
    return json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')


def post_keywords(post):
    """Editorial topic labels, not a Google ranking mechanism."""
    return list(dict.fromkeys([post['primary_keyword'], *post['secondary_keywords']]))


def post_author(post):
    return post.get('author', {'@type': 'Organization', 'name': 'Command Marketing', 'url': ORIGIN + '/blog'})


def faq_graph(post, rendered, url):
    """Only opted-in, visible FAQ text is copied into structured data."""
    if not post.get('faq_schema'):
        return None
    heading = next((node for node in rendered.find_all('h2') if node.get_text(strip=True) == '자주 묻는 질문'), None)
    assert heading, post['slug']
    questions = []
    current = None
    for node in heading.find_next_siblings():
        if node.name == 'h2':
            break
        if node.name == 'h3':
            current = {'@type': 'Question', 'name': node.get_text(' ', strip=True), 'acceptedAnswer': {'@type': 'Answer', 'text': ''}}
            questions.append(current)
        elif current is not None:
            text = node.get_text(' ', strip=True)
            if text:
                current['acceptedAnswer']['text'] += (' ' if current['acceptedAnswer']['text'] else '') + text
    assert questions and all(q['acceptedAnswer']['text'] for q in questions), post['slug']
    return {'@type': 'FAQPage', '@id': url + '#faq', 'mainEntity': questions}


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
    author_name = post_author(post)['name'] if post else 'Command Marketing'
    return f'''<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} | Command Marketing</title>
<meta name="description" content="{escape(description, quote=True)}">
<meta name="author" content="{escape(author_name, quote=True)}"><meta name="publisher" content="TROE">
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
    if post.get('series_key') == 'command-marketing-os':
        members = sorted(COMMAND_SERIES, key=lambda p: p['series_order'])
        index = next(i for i, member in enumerate(members) if member['slug'] == post['slug'])
        entries = []
        for member in members:
            label = f'{member["series_order"]}. {escape(member["short_title"])}'
            if member['slug'] in BY_SLUG:
                current = ' aria-current="page"' if member['slug'] == post['slug'] else ''
                entry = f'<a href="/blog/{member["slug"]}"{current}>{label}</a>'
            else:
                entry = f'<span class="series-pending">{label} · {member["date"]} 발행 예정</span>'
            entries.append(f'<li>{entry}</li>')
        previous = ''
        if index:
            member = members[index - 1]
            if member['slug'] in BY_SLUG:
                previous = f'<a href="/blog/{member["slug"]}" aria-label="이전 편: {escape(member["short_title"], quote=True)}">← 이전 편</a>'
        following = '<a href="/#contents">책 전체 구성 보기 →</a>'
        if index + 1 < len(members):
            member = members[index + 1]
            if member['slug'] in BY_SLUG:
                following = f'<a href="/blog/{member["slug"]}" aria-label="다음 편: {escape(member["short_title"], quote=True)}">다음 편 →</a>'
            else:
                following = f'<span class="series-pending">다음 편 · {member["date"]} 발행 예정</span>'
        return f'''<nav class="series-nav" aria-label="커맨드 마케팅 OS 연결 시리즈"><p class="series-status">커맨드 마케팅 OS 연결 시리즈 · 현재 {post["series_order"]}/{len(members)}</p><div class="series-pager">{previous}{following}</div>
<details class="series-full-list"><summary>시리즈 전체 {len(members)}편 보기</summary><ol>{''.join(entries)}</ol></details></nav>'''
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
    'jev-engineering-guide': 'review',
    'command-marketing-book-practical-guide': 'review',
    'agentic-ai-harness-loop-graph-jev-marketer-guide': 'review',
}


def consulting_href(post, location='direct'):
    work = WORK_BY_SLUG.get(post['slug'], 'undecided')
    intent = 'education' if post.get('kind') == 'book-series' else 'workflow'
    return f'/consulting?from={post["slug"]}&work={work}&intent={intent}&cta={location}-team'


def cta_primary(post, location, class_name='button primary'):
    position = f'article-{location}' if location != 'mobile' else 'mobile-sticky'
    cta_type = 'book' if post.get('kind') == 'book-series' or post.get('cta_goal') == 'book' else 'team'
    cta_id = f'{location}-{cta_type}'
    if cta_type == 'book':
        label = escape(post.get('book_cta_label', '교보문고에서 책 구매'))
        return f'<a class="{class_name}" href="{escape(PURCHASE_URL, quote=True)}" target="_blank" rel="noreferrer" data-cta="purchase" data-position="{position}" data-cta-id="{cta_id}">{label}</a>'
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
        resource_path = '/resources/rgctor-worksheet' if post['slug'] in ('rgctor-content-workflow', 'marketer-ai-agent-workflow-design', 'why-marketers-need-ai-agents', 'jev-engineering-guide', 'command-marketing-book-practical-guide', 'agentic-ai-harness-loop-graph-jev-marketer-guide') else '/resources/content-search-checklist'
        resource_label = 'R-G-C-T-O-R 업무 지시서 워크시트 보기' if resource_path.endswith('rgctor-worksheet') else '콘텐츠·검색 점검표 보기'
        context_link = ''
        resource_id = resource_path.rsplit('/', 1)[-1]
        secondary = f'<a class="button secondary" href="{resource_path}" data-resource-id="{resource_id}" data-cta-id="{location}-resource" data-position="{position}">{resource_label}</a>'
    if location == 'inline':
        if post.get('kind') == 'book-series':
            heading = '읽은 내용을 내 업무에 대입해 보세요.'
            copy = '책의 전체 구성에서 지금 필요한 주제를 고르세요. 팀 교육이나 조직 적용이 필요하다면 현재 업무 범위로 문의할 수 있습니다.'
        else:
            heading = '지금 읽은 기준으로 업무 한 가지를 정리해 보세요.'
            copy = '업무 지시서 워크시트에 목표·입력·검수 기준을 적어 보세요. 팀 단위로 적용하려면 현재 운영 흐름을 바탕으로 문의할 수 있습니다.' if resource_path.endswith('rgctor-worksheet') else '콘텐츠·검색 점검표로 현재 게시물을 확인해 보세요. 팀 단위 검수가 필요하면 현재 운영 흐름을 바탕으로 문의할 수 있습니다.'
    if post.get('cta_goal') == 'book':
        content = post['cta_copy'][location]
        heading = escape(content['heading'])
        copy = escape(content['copy'])
        context_link = ''
        secondary = f'<a class="button secondary" href="/#contents" data-cta="preview" data-cta-id="{location}-contents" data-position="{position}">책 전체 목차 보기</a>'
    label = '실행 기준 이어 보기' if location == 'inline' else '다음 단계'
    return f'''<section class="article-cta article-cta-{location}"{' id="article-end"' if location == 'end' else ''} aria-label="{label}">
<p class="eyebrow">{label}</p><h3>{heading}</h3><p>{copy}</p>{context_link}<div class="article-cta-actions">{primary}{secondary}</div></section>'''


def mobile_cta(post):
    return f'''<aside class="article-mobile-cta" aria-label="빠른 다음 행동" hidden>
{cta_primary(post, 'mobile', 'article-mobile-cta-link button primary')}<button class="article-mobile-cta-close" type="button" aria-label="빠른 다음 행동 닫기">×</button></aside>'''


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
    # Otherwise Markdown treats [2] [3] as one reference link: label 2, URL 3.
    src = re.sub(r'(\[\d+\])[ \t]+(?=\[\d+\](?!:))', r'\1, ', src)
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
               'articleSection': post['category'], 'author': post_author(post),
               'publisher': {'@type': 'Organization', 'name': 'TROE', 'url': 'https://troe.kr/'},
               'isPartOf': {'@type': 'Blog', '@id': ORIGIN + '/blog#blog', 'name': 'Command Marketing 블로그'},
               'citation': [ref_url for _, ref_url, _ in refs]}
    article['alternativeHeadline'] = post['seo_title']
    article['abstract'] = post['search_summary']
    article['keywords'] = post_keywords(post)
    article['about'] = [{'@type': 'Thing', 'name': keyword} for keyword in post_keywords(post)]
    is_series = post.get('kind') == 'book-series'
    if is_series or post.get('book_based'):
        article['isBasedOn'] = BOOK
        article['citation'].append(BOOK)
    graph = {'@context': 'https://schema.org', '@graph': [article, breadcrumb_graph(post)]}
    faq = faq_graph(post, rendered, url)
    if faq:
        graph['@graph'].append(faq)
    related = ''.join(card(BY_SLUG[slug]) for slug in post['related'])
    if is_series:
        disclosure = SERIES_DISCLOSURE
        disclosure_short = SERIES_SHORT_DISCLOSURE
    elif post.get('book_overview'):
        disclosure = post['disclosure']
        disclosure_short = post['disclosure_short']
    elif post.get('book_based'):
        disclosure = BOOK_BASED_GUIDE_DISCLOSURE
        disclosure_short = BOOK_BASED_GUIDE_SHORT_DISCLOSURE
    else:
        disclosure = post.get('disclosure', GUIDE_DISCLOSURE)
        disclosure_short = post.get('disclosure_short', 'Command Marketing 편집 · AI 초안 활용 · 공개 출처 기반 실무 응용 · 도서 요약 아님')
    date_text = f'게시: <time datetime="{post["date"]}">{post["date"]}</time> · 검토·수정: <time datetime="{post.get("modified", post["date"])}">{post.get("modified", post["date"])}</time>'
    topics = post_keywords(post)
    topic_labels = ''.join(f'<li>{escape(keyword)}</li>' for keyword in topics[:3])
    remaining_topics = ''.join(f'<li>{escape(keyword)}</li>' for keyword in topics[3:])
    topic_more = f'<details class="article-topic-details"><summary>주제 {len(topics) - 3}개 더 보기</summary><ul class="article-topics" aria-label="추가 핵심 주제">{remaining_topics}</ul></details>' if remaining_topics else ''
    insert_inline_cta(rendered, article_cta(post, 'inline'))
    html = head(post['seo_title'], post['description'], path, graph, post=post, article_ux=True) + f'''
<body class="blog-page" data-page-type="blog_article" data-ui-variant="ux-v1" data-content-group="{'book_series' if is_series else 'practical_guide'}" data-series-order="{post.get('series_order', '')}" data-article="{post['slug']}"><a class="skip-link" href="#main">본문으로 이동</a>{HEADER}
<main class="blog-main wrap" id="main">{breadcrumbs(post)}
<header class="blog-heading article-head"><div class="article-head-copy"><p class="eyebrow">{escape(post['category'])}</p><h1>{escape(post['title'])}</h1>
<p class="article-meta"><span>검토: <time datetime="{post.get('modified', post['date'])}">{post.get('modified', post['date'])}</time></span><span>약 {reading}분 읽기</span></p></div>
<figure class="article-head-visual">{picture(post, hero=True)}<figcaption>AI 생성 카툰 · 손글씨</figcaption></figure>
<div class="article-head-details"><p class="article-summary">{escape(post['search_summary'])}</p><ul class="article-topics" aria-label="이 글의 핵심 주제">{topic_labels}</ul>{topic_more}
<p class="article-disclosure-short">{escape(disclosure_short)}</p><details class="article-disclosure-details"><summary>편집·출처 고지 자세히</summary><p>{escape(disclosure)}</p><p>{date_text}</p></details></div></header>
{series_navigation(post)}
<div class="article-layout"><aside class="article-toc" aria-label="글 목차"><nav class="article-toc-desktop" aria-label="이 글의 순서"><p>이 글의 순서</p><ol>{''.join(toc)}</ol></nav>
<details class="article-toc-mobile"><summary>이 글의 순서</summary><ol>{''.join(toc)}</ol></details></aside>
<article class="article-body" aria-label="{escape(post['title'], quote=True)}">{str(rendered)}{article_cta(post, 'end')}</article></div>
{mobile_cta(post)}
<section class="blog-section" style="padding:40px 0 70px" aria-labelledby="related-title"><h2 class="extra-title" id="related-title">함께 읽으면 좋은 글</h2><div class="blog-cards">{related}</div><a class="text-link" href="/blog">블로그 전체 보기 →</a></section></main>{FOOTER}'''
    directory = DIST / 'blog' / post['slug']
    directory.mkdir(parents=True, exist_ok=True)
    validate_cta_layout(BeautifulSoup(html, 'html.parser').select_one('.article-body'))
    (directory / 'index.html').write_text(html)


def topic_navigation(home=False):
    prefix = '#home-' if home else '#'
    links = ''.join(f'<a href="{prefix}{section["id"]}">{escape(section["title"])} <span class="blog-topic-count">{len(section["posts"])}편</span></a>' for section in TOPIC_SECTIONS)
    return f'<nav class="blog-category-nav blog-topic-nav" aria-label="블로그 주제 바로가기">{links}</nav>'


def topic_groups(home=False):
    groups = []
    for section in TOPIC_SECTIONS:
        identifier = ('home-' if home else '') + section['id']
        layout = ' series-cards' if section['sort'] == 'series' else ''
        cards = ''.join(card(post) for post in section['posts'])
        # Preserve old inbound #practical-guides links without adding duplicate cards.
        legacy = '<span id="practical-guides" class="blog-legacy-anchor" aria-hidden="true"></span>' if not home and section['id'] == 'command-marketing-os' else ''
        groups.append(f'''{legacy}<section class="blog-group blog-topic-group" id="{identifier}" data-blog-topic="{section['id']}" aria-labelledby="{identifier}-title">
<header class="blog-topic-heading"><div><p class="eyebrow">{escape(section['eyebrow'])}</p><h2 class="extra-title" id="{identifier}-title">{escape(section['title'])}</h2><p class="section-copy">{escape(section['description'])}</p></div><p class="blog-topic-total">{len(section['posts'])}편</p></header>
<div class="blog-cards{layout}">{cards}</div></section>''')
    return '\n'.join(groups)


ordered = [post for section in TOPIC_SECTIONS for post in section['posts']]
BLOG_TITLE = 'AI Agent·커맨드 마케팅·SEO 실무 블로그'
BLOG_DESCRIPTION = f'AI Agent 도서 활용, 커맨드 마케팅 OS, 조직 협업, Agentic AI 기술, SEO·GEO·AIEO의 {len(POSTS)}편을 주제별로 읽어보세요.'
items = [{'@type': 'ListItem', 'position': i + 1, 'url': ORIGIN + '/blog/' + p['slug'], 'name': p['title']} for i, p in enumerate(ordered)]
graph = {'@context': 'https://schema.org', '@graph': [
    {'@type': 'CollectionPage', '@id': ORIGIN + '/blog#webpage', 'url': ORIGIN + '/blog', 'name': BLOG_TITLE, 'inLanguage': 'ko-KR', 'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(items), 'itemListElement': items}},
    {'@type': 'Blog', '@id': ORIGIN + '/blog#blog', 'url': ORIGIN + '/blog', 'name': 'Command Marketing 블로그', 'inLanguage': 'ko-KR', 'publisher': {'@type': 'Organization', 'name': 'TROE', 'url': 'https://troe.kr/'}}, breadcrumb_graph()]}
index = head(BLOG_TITLE, BLOG_DESCRIPTION, '/blog', graph) + f'''
<body class="blog-page" data-page-type="blog_index" data-content-group="blog_index"><a class="skip-link" href="#main">본문으로 이동</a>{HEADER}<main class="blog-main wrap" id="main">{breadcrumbs()}
<header class="blog-heading"><p class="eyebrow">Command Marketing / Field notes</p><h1>AI Agent의 이해부터,<br>내 업무·팀 운영·검색까지.</h1><p class="section-copy">{len(POSTS)}편을 {len(TOPIC_SECTIONS)}개 주제로 나눴습니다. 책의 핵심을 읽고 개인 OS와 조직 협업을 설계하거나, Agentic AI 기술·검색 최적화부터 필요한 내용을 찾아보세요. 시리즈는 1→2→3, 도입·협업과 기술 글은 최근 게시일순입니다.</p>{topic_navigation()}<p class="blog-disclosure">도서 소개는 『AI Agent를 지휘하는 마케터』의 주제와 구성을 안내합니다. 실무 가이드는 도서의 일반 주제·공개 출처 기반 편집 응용 또는 사용자 제공 원고의 형식 변환이며, 글별 저자·편집·검토 고지를 확인하세요.</p></header>
{topic_groups()}
<div class="article-end"><p class="eyebrow">Read the system</p><h2 class="extra-title">콘텐츠 제작을 반복 가능한 운영으로 바꾸고 싶다면.</h2><p class="section-copy">책의 업무 지시서와 검수·승인 구조를 확인하세요.</p><div class="actions"><a class="button primary" href="/#system">R-G-C-T-O-R 보기</a><a class="button secondary" href="/#diagnosis">내 상황 진단하기</a></div></div></main>{FOOTER}'''
(DIST / 'blog/index.html').write_text(index)

home_section = f'''<section class="blog-section section" id="blog" data-track-section="blog"><div class="wrap"><div class="blog-head"><div><p class="eyebrow">Book · OS · Team · Technology · Search</p><h2 class="section-title">지금 필요한 주제부터,<br>마케팅 AI를 업무로 연결하세요.</h2><p class="section-copy">도서 읽기·실무 활용, 커맨드 마케팅 OS, 조직 협업, Agentic AI 기술, 검색 최적화. {len(POSTS)}편을 {len(TOPIC_SECTIONS)}개 주제로 정리했습니다. 두 시리즈는 순서대로, 나머지는 안내된 읽기 흐름으로 탐색하세요.</p></div><a class="text-link" href="/blog">블로그 전체 보기 →</a></div>{topic_navigation(home=True)}{topic_groups(home=True)}</div></section>'''
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

base_routes = [{'path': '/', 'title': 'AI Agent를 지휘하는 마케터'}, {'path': '/blog', 'title': BLOG_TITLE}] + [{'path': '/blog/' + p['slug'], 'title': p['title']} for p in POSTS]
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
for section in TOPIC_SECTIONS:
    group = section['posts']
    llms += f'\n## {section["title"]} {len(group)}편\n\n'
    llms += f'- [{section["title"]} 목록]({ORIGIN}/blog#{section["id"]}): {section["description"]}\n'
    llms += '\n'.join(f'- [{post["seo_title"]}]({ORIGIN}/blog/{post["slug"]}): {post["search_summary"]}' for post in group) + '\n'
llms += f'\n## 공개 편집 자료와 팀 적용 문의\n\n- [R-G-C-T-O-R 업무 지시서 워크시트]({ORIGIN}/resources/rgctor-worksheet): 공개 편집 응용 자료이며 도서 본문을 대신하지 않습니다.\n- [콘텐츠·검색 점검표]({ORIGIN}/resources/content-search-checklist): 공개 편집 응용 자료이며 도서 본문을 대신하지 않습니다.\n- [팀 적용 문의]({ORIGIN}/consulting): 콘텐츠 검수·운영 체계의 적용 범위를 문의하는 경로입니다.\n'
llms += f'\n## 검색 보조 문서\n\n- [XML 사이트맵]({ORIGIN}/sitemap.xml): 현재 색인 대상 정규 URL {len(indexable_routes)}개와 대표 이미지\n- [크롤러 접근 정책]({ORIGIN}/robots.txt): 검색·사용자 요청 크롤러와 모델 학습 크롤러의 정책 구분\n'
llms += f'\n문서 검토 기준일: {REVIEWED}. 각 페이지의 최종 콘텐츠 수정일은 사이트맵과 글의 게시·검토 표시를 참고하세요. llms.txt는 보조 문서이며 검색 노출이나 AI 인용을 보장하지 않습니다.\n'
for path in (ROOT / 'llms.txt', DIST / 'llms.txt'):
    path.write_text(llms)
(DIST / '404.html').write_text(head('페이지를 찾을 수 없습니다', '요청한 페이지가 없거나 이동되었습니다. 도서 소개 또는 블로그 목록에서 다시 탐색하세요.', noindex=True) + f'<body class="blog-page">{HEADER}<main class="wrap not-found" id="main"><p class="eyebrow">404 / NOT FOUND</p><h1>이 페이지는 찾을 수 없습니다.</h1><p class="section-copy">도서 소개나 블로그 목록에서 필요한 내용을 다시 찾아보세요.</p><div class="actions"><a class="button primary" href="/">도서 홈</a><a class="button secondary" href="/blog">블로그 목록</a></div></main>{FOOTER}')
print(f'Static blog built: {len(POSTS)} articles ({len(SERIES)} book series), {len(indexable_routes)} indexable pages. Origin: {ORIGIN}')
