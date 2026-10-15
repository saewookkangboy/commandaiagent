"""Check static blog integrity without changing site state or contacting analytics."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from datetime import date
import json
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
ORIGIN = 'https://book.allrounder.im'
posts = json.loads((ROOT / 'content/blog/posts.json').read_text())
assert len(posts) == 10
assert len({post['slug'] for post in posts}) == len(posts)
assert len([p for p in posts if p['kind'] == 'book-series']) == 3
assert len({post['description'] for post in posts}) == len(posts)
assert len({post['image'] for post in posts}) == len(posts)
assert len({post['seo_title'] for post in posts}) == len(posts)
assert len({post['primary_keyword'] for post in posts}) == len(posts)
assert len({post['search_summary'] for post in posts}) == len(posts)


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
for file, soup in htmls.items():
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
    refs = set(re.findall(r'^\[(\d+)\]:\s+https?://\S+\s+"[^"\n]+"\s*$', source, re.M))
    assert len(refs) >= 2, slug
    inline_source = re.sub(r'^\[\d+\]:.*$', '', source, flags=re.M)
    used = set(re.findall(r'\[(\d+)\]', inline_source))
    assert used <= refs, (slug, used - refs)
    soup = htmls[DIST / 'blog' / slug / 'index.html']
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
    graph = json.loads(soup.select_one('script[type="application/ld+json"]').string)
    article = next(row for row in graph['@graph'] if row['@type'] == 'BlogPosting')
    assert article['image']['url'] == og
    assert article['author']['name'] == 'Command Marketing'
    assert article['headline'] == post['title']
    assert article['alternativeHeadline'] == post['seo_title']
    assert article['abstract'] == post['search_summary']
    assert article['description'] == post['description']
    assert article['keywords'] == keywords
    assert [topic['name'] for topic in article['about']] == keywords
    if post['kind'] == 'book-series':
        assert article['isBasedOn']['name'] == 'AI Agent를 지휘하는 마케터'
        assert len(soup.select('.series-nav [aria-current="page"]')) == 1
        assert len(soup.select('.series-nav ol a')) == 3
        assert len(re.findall(r'도서 p', source)) >= 4
        assert '편집 응용' in source and '도서 근거와 편집 범위' in source
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
assert '책 소개 시리즈 3편은 제공 PDF를 요약' in llms
assert not list(DIST.rglob('*.pdf'))
assert not list((ROOT / 'content').rglob('*.pdf'))
assert set(json.loads((ROOT / 'content/analytics-events.json').read_text())['article_slugs']) == {p['slug'] for p in posts}
print(f'PASS: {len(posts)} articles, {len(urls)} indexable URLs, unique sharing images, source references, series navigation, analytics slugs, all local links, no source PDF exposure')
