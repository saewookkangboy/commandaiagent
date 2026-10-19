"""Check static blog integrity without changing site state or contacting analytics."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from datetime import date
import json
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from article_cta import validate_cta_layout

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
ORIGIN = 'https://book.allrounder.im'
posts = json.loads((ROOT / 'content/blog/posts.json').read_text())
assert len(posts) >= 14
assert 'book-ai-agent-roles-reading-guide' in {post['slug'] for post in posts}
assert len({post['slug'] for post in posts}) == len(posts)
assert len([p for p in posts if p['kind'] == 'book-series']) == 3
assert len({post['description'] for post in posts}) == len(posts)
assert len({post['image'] for post in posts}) == len(posts)
assert len({post['seo_title'] for post in posts}) == len(posts)
assert len({post['primary_keyword'] for post in posts}) == len(posts)
assert len({post['search_summary'] for post in posts}) == len(posts)

SOURCE_PROVENANCE_MARKERS = ('pdf', '최종 내지', '최종내지', '페이지 마커', '인쇄 페이지', 'footer')
BOOK_TITLE = 'AI Agent를 지휘하는 마케터'
PUBLIC_SOURCE_REQUIREMENTS = {
    'book-command-marketer-01': ('https://book.allrounder.im/', 'https://developers.google.com/search/docs/appearance/ai-features'),
    'book-command-marketer-02': ('https://book.allrounder.im/', 'https://developers.google.com/search/docs/appearance/ai-features'),
    'book-command-marketer-03': ('https://book.allrounder.im/', 'https://developers.google.com/search/docs/appearance/ai-features'),
    'command-marketing-book-practical-guide': ('https://book.allrounder.im/', 'https://www.anthropic.com/engineering/building-effective-agents'),
    'book-ai-agent-roles-reading-guide': ('https://book.allrounder.im/', 'https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=402869781'),
}


def local_file(path):
    target = DIST / unquote(path).lstrip('/')
    if target.is_dir():
        return target / 'index.html'
    if target.is_file():
        return target
    if not target.suffix and (target / 'index.html').is_file():
        return target / 'index.html'
    return target


htmls = {p: BeautifulSoup(p.read_text(), 'html.parser') for p in DIST.rglob('*.html')}
home = htmls[DIST / 'index.html']
verification = home.select('meta[name="naver-site-verification"]')
assert len(verification) == 1, 'Naver ownership verification tag is missing or duplicated'
assert verification[0].parent is home.head, 'Naver verification tag must be in the initial HTML head'
assert verification[0]['content'] == 'b8f0f6212f1c00a481d9634ce7eec49d0afe4b46'
for file, soup in htmls.items():
    visible_html = soup.get_text(' ', strip=True).lower()
    assert all(marker not in visible_html for marker in SOURCE_PROVENANCE_MARKERS), (file, 'provided-file provenance is visible')
    assert len(soup.select('h1')) == 1, file
    ids = [tag['id'] for tag in soup.select('[id]')]
    assert len(ids) == len(set(ids)), (file, 'duplicate IDs')
    for tag in soup.select('script[type="application/ld+json"]'):
        json.loads(tag.string)
    for tag in soup.select('a[href],img[src],source[srcset],script[src],link[href]'):
        href = tag.get('href') or tag.get('src') or tag.get('srcset')
        u = urlsplit(href)
        if u.netloc and u.netloc != urlsplit(ORIGIN).netloc:
            continue
        if u.scheme and u.scheme not in ('http', 'https'):
            continue
        target = local_file(u.path) if u.path else file
        assert target.is_file(), (file, href, target)
        if u.fragment and target.suffix == '.html':
            dom = htmls.get(target) or BeautifulSoup(target.read_text(), 'html.parser')
            assert dom.find(id=unquote(u.fragment)), (file, href, 'missing anchor')

for post in posts:
    slug = post['slug']
    source = (ROOT / 'content/blog' / f'{slug}.md').read_text()
    assert source.splitlines()[0] == '# ' + post['title']
    source_without_reference_definitions = re.sub(r'^\[\d+\]:.*$', '', source, flags=re.M)
    source_visible = re.sub(r'\]\([^)]+\)', ']', source_without_reference_definitions).lower()
    assert all(marker not in source_visible for marker in SOURCE_PROVENANCE_MARKERS), (slug, 'provided-file provenance is in the manuscript')
    reference_entries = re.findall(r'^\[(\d+)\]:\s+(https?://\S+)\s+"[^"\n]+"\s*$', source, re.M)
    refs = {number for number, _ in reference_entries}
    ref_urls = {url for _, url in reference_entries}
    assert len(refs) >= 2, slug
    assert all(url in ref_urls for url in PUBLIC_SOURCE_REQUIREMENTS.get(slug, ())), (slug, ref_urls)
    used = set(re.findall(r'\[(\d+)\]', source_without_reference_definitions))
    assert used <= refs, (slug, used - refs)
    soup = htmls[DIST / 'blog' / slug / 'index.html']
    validate_cta_layout(soup.select_one('.article-body'))
    assert soup.h1.get_text() == post['title']
    assert soup.select_one('link[rel="canonical"]')['href'] == ORIGIN + '/blog/' + slug
    assert soup.select_one('meta[name="description"]')['content'] == post['description']
    assert soup.title.get_text() == post['seo_title'] + ' | Command Marketing'
    assert len(soup.title.get_text()) <= 60, (slug, 'editorial title budget, not a ranking rule')
    assert 70 <= len(post['description']) <= 160, slug
    assert soup.select_one('meta[property="og:title"]')['content'] == post['seo_title']
    assert soup.select_one('meta[name="twitter:title"]')['content'] == post['seo_title']
    for selector in ('meta[property="og:description"]', 'meta[name="twitter:description"]'):
        assert soup.select_one(selector)['content'] == post['description']
    keywords = [post['primary_keyword'], *post['secondary_keywords']]
    assert 5 <= len(keywords) <= 7 and len(set(keywords)) == len(keywords)
    assert all(keyword and keyword == keyword.strip() and ',' not in keyword for keyword in keywords)
    assert soup.select_one('meta[name="keywords"]')['content'] == ', '.join(keywords)
    assert [tag['content'] for tag in soup.select('meta[property="article:tag"]')] == keywords
    assert soup.select_one('meta[property="article:section"]')['content'] == post['category']
    assert soup.select_one('.article-summary').get_text() == post['search_summary']
    assert [tag.get_text() for tag in soup.select('.article-topics li')] == keywords
    assert post['primary_keyword'] in post['description']
    assert post['primary_keyword'] in post['search_summary']
    og = soup.select_one('meta[property="og:image"]')['content']
    assert og == ORIGIN + post['image_jpg']
    assert soup.select_one('meta[name="twitter:image"]')['content'] == og
    image = soup.select_one('.article-head img')
    assert image['src'] == post['image_jpg'] and image['alt'] == post['image_alt']
    assert image['loading'] == 'eager' and image['width'] == '1200' and image['height'] == '675'
    assert len(soup.select('.article-body h2')) >= 4
    assert '[1]' not in soup.select_one('.article-body').get_text(), (slug, 'unresolved reference')
    reference_urls = dict(reference_entries)
    rendered_reference_numbers = set()
    for link in soup.select('.article-body a[href]'):
        number = link.get_text(strip=True)
        if re.fullmatch(r'\d+', number):
            assert number in reference_urls and link['href'] == reference_urls[number], (slug, 'mismatched inline reference', number, link['href'])
            rendered_reference_numbers.add(number)
    named_references = set()
    for label, number in re.findall(r'\[([^\[\]\n]+)\]\[(\d+)\]', source):
        if not label.isdigit():
            assert any(a.get_text(strip=True) == label and a['href'] == reference_urls[number] for a in soup.select('.article-body a[href]')), (slug, 'mismatched named reference', label)
            named_references.add(number)
    assert used <= rendered_reference_numbers | named_references, (slug, 'missing inline reference', used - rendered_reference_numbers - named_references)
    graph = json.loads(soup.select_one('script[type="application/ld+json"]').string)
    article = next(row for row in graph['@graph'] if row['@type'] == 'BlogPosting')
    assert article['image']['url'] == og
    author = post.get('author', {'@type': 'Organization', 'name': 'Command Marketing', 'url': ORIGIN + '/blog'})
    assert article['author'] == author
    assert soup.select_one('meta[name="author"]')['content'] == author['name']
    assert article['headline'] == post['title']
    assert article['alternativeHeadline'] == post['seo_title']
    assert article['abstract'] == post['search_summary']
    assert article['description'] == post['description']
    assert article['keywords'] == keywords
    assert [topic['name'] for topic in article['about']] == keywords
    assert article['datePublished'] == post['date']
    assert article['dateModified'] == post.get('modified', post['date'])
    if slug == 'jev-engineering-guide':
        assert author['@type'] == 'Person' and author['name'] == '박충효'
        assert post['date'] == '2026-10-02' and post['source_modified'] == '2026-10-06'
        assert post['disclosure_short'] == soup.select_one('.article-disclosure-short').get_text()
        assert post['disclosure'] == soup.select_one('.article-disclosure-details p').get_text()
        assert len(soup.select('.article-body table')) == 3
        assert len(soup.select('.article-body ol')) == 2  # six steps + rendered source list
        faq = next(row for row in graph['@graph'] if row['@type'] == 'FAQPage')
        assert len(faq['mainEntity']) == 6
        heading = next(h for h in soup.select('.article-body h2') if h.get_text() == '자주 묻는 질문')
        visible = []
        for node in heading.find_next_siblings():
            if node.name == 'h2':
                break
            if node.name == 'h3':
                visible.append((node.get_text(' ', strip=True), node.find_next_sibling('p').get_text(' ', strip=True)))
        assert visible == [(q['name'], q['acceptedAnswer']['text']) for q in faq['mainEntity']]
        assert '별도의 confidence는 없습니다' in faq['mainEntity'][1]['acceptedAnswer']['text']
        assert any('/resources/rgctor-worksheet' in a['href'] for a in soup.select('.article-cta a[href]'))
        context_links = soup.select('.article-cta a[data-consulting-path], .article-mobile-cta a[data-consulting-path]')
        assert len(context_links) == 3
        assert all('from=jev-engineering-guide' in a['href'] and 'work=review' in a['href'] for a in context_links)
    if slug == 'command-marketing-book-practical-guide':
        assert post['kind'] == 'guide' and post['book_based'] is True
        assert article['isBasedOn']['name'] == 'AI Agent를 지휘하는 마케터'
        assert author['@type'] == 'Organization' and not soup.select('.series-nav')
        disclosure_short = soup.select_one('.article-disclosure-short').get_text()
        disclosure_detail = soup.select_one('.article-disclosure-details p').get_text()
        assert 'AI 초안 활용' in disclosure_short and '도서 주제를 바탕으로 한 실무 응용' in disclosure_short
        assert 'AI 초안 활용' in disclosure_detail and '저자가 직접 집필한 글은 아닙니다' in disclosure_detail
        assert '함께 읽을 내용과 적용 범위' in source and '편집 응용' in source
        assert BOOK_TITLE in source and '박충효' in source and 'AI 초안' in source
        assert len(soup.select('.article-body pre code')) == 1
        assert len(next(row for row in graph['@graph'] if row['@type'] == 'FAQPage')['mainEntity']) == 5
        context_links = soup.select('.article-cta a[data-consulting-path], .article-mobile-cta a[data-consulting-path]')
        assert len(context_links) == 3
        assert all(f'from={slug}' in a['href'] and 'work=review' in a['href'] and 'intent=workflow' in a['href'] for a in context_links)
        assert len(soup.select('.article-cta a[href="/resources/rgctor-worksheet"]')) == 2
    if slug == 'agentic-ai-harness-loop-graph-jev-marketer-guide':
        assert post['date'] == '2026-10-17' and post['kind'] == 'guide'
        assert author['@type'] == 'Organization'
        assert post['disclosure'] == soup.select_one('.article-disclosure-details p').get_text()
        assert len(soup.select('.article-body pre code')) == 4
        assert '필수 교체 단계가 아닙니다' in source
        assert '확신도는 허가나 실제 정답률이 아닙니다' in source
        assert len(next(row for row in graph['@graph'] if row['@type'] == 'FAQPage')['mainEntity']) == 6
        assert len(refs) == 9
        context_links = soup.select('.article-cta a[data-consulting-path], .article-mobile-cta a[data-consulting-path]')
        assert len(context_links) == 3
        assert all(f'from={slug}' in a['href'] and 'work=review' in a['href'] and 'intent=workflow' in a['href'] for a in context_links)
        assert len(soup.select('.article-cta a[href="/resources/rgctor-worksheet"]')) == 2
    if slug == 'book-ai-agent-roles-reading-guide':
        assert post['kind'] == 'guide' and post['book_based'] and post['book_overview']
        assert article['isBasedOn']['name'] == BOOK_TITLE
        assert author['@type'] == 'Organization' and not soup.select('.series-nav')
        assert post['disclosure'] == soup.select_one('.article-disclosure-details p').get_text()
        assert post['disclosure_short'] == soup.select_one('.article-disclosure-short').get_text()
        role_headings = re.findall(r'^### (\d+)\. (.+ Agent)$', source, re.M)
        assert [int(number) for number, _ in role_headings] == list(range(1, 18))
        assert '17개' in source and '18개' not in source
        assert post['primary_keyword'] == 'AI Agent 역할별 특징'
        assert post['seo_title'] == 'AI Agent 역할별 특징: 마케팅 업무 17가지와 책 읽기 가이드'
        for term in ('마케팅 AI 에이전트 역할', '마케팅 AI 에이전트 업무', '고객 인사이트 AI 에이전트',
                     '경쟁사 분석 AI 에이전트', '콘텐츠 기획 AI 에이전트', 'CRM AI 에이전트 역할',
                     '마케팅 데이터 리포팅 AI 에이전트', 'AI 에이전트 검수 기준'):
            assert term in source, (slug, 'missing natural-language topic', term)
        faq = next(row for row in graph['@graph'] if row['@type'] == 'FAQPage')['mainEntity']
        assert len(faq) == 6 and len({row['name'] for row in faq}) == 6
        heading = next(h for h in soup.select('.article-body h2') if h.get_text() == '자주 묻는 질문')
        visible = []
        for node in heading.find_next_siblings():
            if node.name == 'h2':
                break
            if node.name == 'h3':
                visible.append((node.get_text(' ', strip=True), node.find_next_sibling('p').get_text(' ', strip=True)))
        assert visible == [(row['name'], row['acceptedAnswer']['text']) for row in faq]
        for linked in ('book-command-marketer-02', 'command-marketing-book-practical-guide'):
            linked_source = (ROOT / 'content/blog' / f'{linked}.md').read_text()
            assert linked_source.count('](/blog/' + slug + ')') == 1
            assert '마케팅 AI 에이전트 17가지 역할과 독서 가이드' in linked_source
        for linked in ('why-marketers-need-ai-agents', 'marketer-ai-agent-workflow-design'):
            assert '](/blog/' + linked + ')' in source
        inline = soup.select_one('.article-cta-inline')
        end = soup.select_one('.article-cta-end')
        assert inline and end and 'Part 5. 랜딩' in inline.find_next_sibling('h2').get_text()
        assert len(inline.find_all_previous('h3')) == 8
        for location in ('inline', 'end'):
            link = soup.select_one(f'.article-cta-{location} a[data-cta-id="{location}-book"]')
            assert link.get_text() == '책을 통해서 확인해보세요'
            assert link['href'] == 'https://product.kyobobook.co.kr/detail/S000221439823?LINK=PLP'
            assert link['data-cta'] == 'purchase' and link['data-position'] == f'article-{location}'
            assert soup.select_one(f'.article-cta-{location} a[data-cta-id="{location}-contents"]')['href'] == '/#contents'
        assert soup.select_one('.article-mobile-cta a')['data-cta-id'] == 'mobile-book'
        assert not soup.select('.article-cta a[data-consulting-path]')
    if post['kind'] == 'book-series':
        assert article['isBasedOn']['name'] == 'AI Agent를 지휘하는 마케터'
        assert len(soup.select('.series-nav [aria-current="page"]')) == 1
        assert len(soup.select('.series-nav ol a')) == 3
        assert '편집 응용' in source and '함께 읽을 내용과 적용 범위' in source
        assert BOOK_TITLE in source and '박충효' in source and 'AI 초안' in source
        assert 'AI 초안 활용' in soup.select_one('.article-disclosure-short').get_text()
        assert '저자가 직접 집필한 블로그 글은 아닙니다' in soup.select_one('.article-disclosure-details p').get_text()
    print('PASS', slug)

index = htmls[DIST / 'blog/index.html']
assert len(index.select('#book-series .blog-card')) == 3
assert len(index.select('#practical-guides .blog-card')) == len([p for p in posts if p['kind'] != 'book-series'])
assert len(htmls[DIST / 'index.html'].select('#blog .blog-card')) == len(posts)
assert len(json.loads((DIST / 'manus-routes.json').read_text())['routes']) == len(posts) + 7
urls = [node.text for node in ET.parse(DIST / 'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert len(urls) == len(posts) + 6 and len(set(urls)) == len(urls)
extra_paths = ['/consulting','/resources','/resources/rgctor-worksheet','/resources/content-search-checklist']
assert set(urls) == {ORIGIN + '/', ORIGIN + '/blog'} | {ORIGIN + '/blog/' + p['slug'] for p in posts} | {ORIGIN + path for path in extra_paths}
assert ORIGIN + '/privacy' not in urls
assert htmls[DIST / 'privacy/index.html'].select_one('meta[name=robots]')['content'].startswith('noindex')
assert (ROOT / 'sitemap.xml').read_bytes() == (DIST / 'sitemap.xml').read_bytes()
ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'image': 'http://www.google.com/schemas/sitemap-image/1.1'}
site = json.loads((ROOT / 'content/site.json').read_text())
expected_modified = {ORIGIN + '/': site['home_modified'], ORIGIN + '/blog': max(p.get('modified', p['date']) for p in posts)}
expected_images = {ORIGIN + '/': ORIGIN + '/assets/book-flat.jpg'}
funnel = json.loads((ROOT / 'content/funnel.json').read_text())
expected_modified.update({ORIGIN + path: funnel['modified'] for path in extra_paths})
for post in posts:
    url = ORIGIN + '/blog/' + post['slug']
    expected_modified[url] = post.get('modified', post['date'])
    expected_images[url] = ORIGIN + post['image_jpg']
for node in ET.parse(DIST / 'sitemap.xml').getroot().findall('sm:url', ns):
    url = node.findtext('sm:loc', namespaces=ns)
    modified = node.findtext('sm:lastmod', namespaces=ns)
    assert modified == expected_modified[url] and date.fromisoformat(modified).isoformat() == modified
    image_urls = [tag.text for tag in node.findall('image:image/image:loc', ns)]
    assert image_urls == ([expected_images[url]] if url in expected_images else [])
    assert local_file(urlsplit(url).path).is_file()
    for image_url in image_urls:
        assert local_file(urlsplit(image_url).path).is_file()
llms = (DIST / 'llms.txt').read_text()
assert (ROOT / 'llms.txt').read_bytes() == (DIST / 'llms.txt').read_bytes()
assert llms.startswith((ROOT / 'content/llms-base.md').read_text().rstrip())
expected_reviewed = max(site['llms_reviewed'], site['home_modified'], *expected_modified.values())
assert re.findall(r'^문서 검토 기준일: ([0-9-]+)\.', llms, re.M) == [expected_reviewed], 'Stale llms review date; rebuild search documents'
assert all(p['slug'] in llms for p in posts)
assert llms.count('## 도서 소개 시리즈 3편') == 1
assert llms.count(f'## SEO·GEO·AIEO 실무 가이드 {len(posts)-3}편') == 1
assert len(re.findall(r'^# ', llms, re.M)) == 1
intro, *link_sections = re.split(r'^## [^\n]+\n', llms, flags=re.M)
assert intro.startswith('# AI Agent를 지휘하는 마케터\n\n> ')
for label in ('도서와 운영 관점', '업무 지시서와 도서 구성', '대상 독자와 읽기 방식',
              '도입 판단과 정밀 설계의 구분', '검색·콘텐츠 운영의 범위',
              '도서 소개와 편집 콘텐츠', '자료 접근과 문의의 의미', '인용과 해석 기준'):
    assert '**' + label + '.**' in intro, ('Missing pre-H2 llms detail', label)
assert len(link_sections) >= 5
for section in link_sections:
    assert section.lstrip().startswith('- ['), 'H2 llms sections must begin with a link list'
    assert re.search(r'^- \[[^\]]+\]\([^\s)]+\): .+', section, re.M)
for post in posts:
    assert f'[{post["seo_title"]}]({ORIGIN}/blog/{post["slug"]}): {post["search_summary"]}' in llms
for href in re.findall(r'\[[^\]]+\]\(([^\s)]+)\)', llms):
    url = urlsplit(href)
    if url.netloc == urlsplit(ORIGIN).netloc:
        target = local_file(url.path)
        assert target.is_file(), href
        if url.fragment:
            assert BeautifulSoup(target.read_text(), 'html.parser').find(id=unquote(url.fragment)), href
assert '도서 발췌나 저자의 직접 발언이 아닙니다' in llms
assert '책 소개 시리즈 3편은 『AI Agent를 지휘하는 마케터』의 주제와 구성을 소개하는 편집 글입니다' in llms
assert all(marker not in llms.lower() for marker in SOURCE_PROVENANCE_MARKERS), 'provided-file provenance is in llms.txt'
assert '박충효·TROE 표기의 사용자 제공 HTML 원고' in llms
assert 'Jev 입문을 제외한' in llms and '**결정 모델과 Jev Engineering.**' in intro
assert not list(DIST.rglob('*.pdf'))
assert not list((ROOT / 'content').rglob('*.pdf'))
assert set(json.loads((ROOT / 'content/analytics-events.json').read_text())['article_slugs']) == {p['slug'] for p in posts}
print(f'PASS: {len(posts)} articles, {len(urls)} indexable URLs, unique sharing images, public source references, series navigation, analytics slugs, all local links, no supplied-file provenance')
