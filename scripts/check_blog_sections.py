"""Offline topic discovery checks; every request is local or aborted."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlsplit, unquote
import json
import mimetypes
from playwright.sync_api import sync_playwright
from blog_sections import load_sections

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
ORIGIN = 'https://book.allrounder.im'
POSTS = json.loads((ROOT / 'content/blog/posts.json').read_text())
SOURCE = ROOT / 'content/blog/sections.json'
SECTIONS = load_sections(SOURCE, POSTS)

with TemporaryDirectory() as temporary:
    path = Path(temporary) / 'sections.json'
    examples = []
    original = json.loads(SOURCE.read_text())
    duplicate = deepcopy(original)
    duplicate[1]['slugs'].append(duplicate[0]['slugs'][0])
    examples.append(duplicate)
    missing = deepcopy(original)
    missing[0]['slugs'].pop()
    examples.append(missing)
    unknown = deepcopy(original)
    unknown[0]['slugs'][0] = 'unpublished-unknown-article'
    examples.append(unknown)
    duplicate_id = deepcopy(original)
    duplicate_id[1]['id'] = duplicate_id[0]['id']
    examples.append(duplicate_id)
    mixed_series = deepcopy(original)
    mixed_series[1]['slugs'].append(mixed_series[0]['slugs'][0])
    examples.append(mixed_series)
    for example in examples:
        path.write_text(json.dumps(example))
        try:
            load_sections(path, POSTS)
        except AssertionError:
            pass
        else:
            raise AssertionError('Invalid topic classification was accepted.')
    shuffled = deepcopy(original)
    for section in shuffled:
        if section['sort'] == 'series':
            section['slugs'].reverse()
    path.write_text(json.dumps(shuffled))
    sorted_sections = load_sections(path, POSTS)
    assert [p['series_order'] for s in sorted_sections if s['sort'] == 'series' for p in s['posts']] == [1, 2, 3]
print('PASS missing/duplicate/unknown topics, mixed series and deterministic order', flush=True)

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    for width in (360, 390, 768, 1440):
        context = browser.new_context(viewport={'width': width, 'height': 900}, reduced_motion='reduce')
        context.add_init_script('window.commandTrackingEnabled=false;')
        outside = []
        def route_request(route):
            url = urlsplit(route.request.url)
            if url.hostname != 'book.allrounder.im':
                outside.append(route.request.url)
                route.abort()
                return
            path = DIST / unquote(url.path).lstrip('/')
            if path.is_dir():
                path = path / 'index.html'
            assert path.is_file(), path
            route.fulfill(status=200, path=str(path), content_type=mimetypes.guess_type(path)[0] or 'application/octet-stream')
        context.route('**/*', route_request)
        page = context.new_page()
        for route in ('/', '/blog'):
            page.goto(ORIGIN + route)
            scope = '#blog' if route == '/' else '.blog-main'
            nav = page.locator(scope + ' .blog-topic-nav')
            assert nav.locator('a').count() == len(SECTIONS)
            assert page.locator(scope + ' .blog-topic-group .blog-card').count() == len(POSTS)
            # The original home has a separate quickstart min-content overflow at
            # 360px. Check this change's topic region, not that unchanged section.
            overflowing = page.locator(scope).evaluate('''root => [root, ...root.querySelectorAll('*')].filter(node => {
                const rect = node.getBoundingClientRect();
                return rect.width > 0 && (rect.left < -1 || rect.right > innerWidth + 1);
            }).map(node => ({tag: node.tagName, className: node.className}))''')
            assert not overflowing, (width, route, overflowing)
            for link in nav.locator('a').all():
                box = link.bounding_box()
                assert box and box['height'] >= 44 and box['x'] >= 0 and box['x'] + box['width'] <= width + 1, (width, route, box)
                link.focus()
                assert link.evaluate('(node) => node === document.activeElement')
                destination = link.get_attribute('href')
                link.press('Enter')
                assert page.url.endswith(destination)
                target = page.locator(destination)
                assert target.count() == 1
                top = target.bounding_box()['y']
                header = page.locator('.site-head').bounding_box()['height']
                assert top >= header - 2, (width, route, destination, top, header)
            if route == '/blog':
                page.goto(ORIGIN + '/blog#practical-guides')
                assert page.locator('#practical-guides').count() == 1
                assert page.locator('#book-series .blog-card').count() == 5
        assert not outside, outside
        context.close()
        print(f'PASS {width}px: all topics,44px controls,keyboard anchors,header clearance,no topic overflow or external requests', flush=True)
    browser.close()
