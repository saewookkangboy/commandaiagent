"""Check static blog integrity without changing site state or contacting analytics."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
ORIGIN = 'https://book.allrounder.im'
posts = json.loads((ROOT / 'content/blog/posts.json').read_text())
assert len(posts) == 8
assert len({post['slug'] for post in posts}) == 8
assert len([p for p in posts if p['kind'] == 'book-series']) == 3
assert len({post['description'] for post in posts}) == 8
assert len({post['image'] for post in posts}) == 8


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
    og = soup.select_one('meta[property="og:image"]')['content']
    assert og == ORIGIN + post['image_jpg']
    assert soup.select_one('meta[name="twitter:image"]')['content'] == og
    image = soup.select_one('.article-cover img')
    assert image['src'] == post['image_jpg'] and image['alt'] == post['image_alt']
    assert image['loading'] == 'eager' and image['width'] == '1200' and image['height'] == '675'
    assert len(soup.select('.article-body h2')) >= 4
    assert '[1]' not in soup.select_one('.article-body').get_text(), (slug, 'unresolved reference')
    graph = json.loads(soup.select_one('script[type="application/ld+json"]').string)
    article = next(row for row in graph['@graph'] if row['@type'] == 'BlogPosting')
    assert article['image']['url'] == og
    assert article['author']['name'] == 'Command Marketing'
    if post['kind'] == 'book-series':
        assert article['isBasedOn']['name'] == 'AI Agent를 지휘하는 마케터'
        assert len(soup.select('.series-nav [aria-current="page"]')) == 1
        assert len(soup.select('.series-nav ol a')) == 3
        assert len(re.findall(r'도서 p', source)) >= 4
        assert '편집 응용' in source and '도서 근거와 편집 범위' in source
    print('PASS', slug)

index = htmls[DIST / 'blog/index.html']
assert len(index.select('#book-series .blog-card')) == 3
assert len(index.select('#practical-guides .blog-card')) == 5
assert len(htmls[DIST / 'index.html'].select('#blog .blog-card')) == 8
assert len(json.loads((DIST / 'manus-routes.json').read_text())['routes']) == 10
urls = [node.text for node in ET.parse(DIST / 'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
assert len(urls) == 10 and len(set(urls)) == 10
assert set(urls) == {ORIGIN + '/', ORIGIN + '/blog'} | {ORIGIN + '/blog/' + p['slug'] for p in posts}
assert (ROOT / 'sitemap.xml').read_bytes() == (DIST / 'sitemap.xml').read_bytes()
llms = (DIST / 'llms.txt').read_text()
assert all(p['slug'] in llms for p in posts)
assert '도서 발췌나 저자의 직접 발언이 아닙니다' in llms
assert '책 소개 시리즈 3편은 제공 PDF를 요약' in llms
assert not list(DIST.rglob('*.pdf'))
assert not list((ROOT / 'content').rglob('*.pdf'))
print('PASS: 8 articles, 10 URLs, unique sharing images, source references, series navigation, all local links, no source PDF exposure')
