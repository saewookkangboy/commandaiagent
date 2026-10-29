"""Offline series context/CTA/navigation checks; never contact live services."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import mimetypes
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
ORIGIN = 'https://book.allrounder.im'
POSTS = [p for p in json.loads((ROOT / 'content/blog/posts.json').read_text())
         if p.get('series_key')]

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    for post in POSTS:
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        outside, errors = [], []

        def route_handler(route):
            url = urlsplit(route.request.url)
            if url.hostname != 'book.allrounder.im':
                outside.append(route.request.url)
                route.abort()
                return
            path = DIST / unquote(url.path).lstrip('/')
            if path.is_dir():
                path = path / 'index.html'
            if not path.is_file():
                route.fulfill(status=404, path=str(DIST / '404.html'), content_type='text/html')
                return
            route.fulfill(status=200, path=str(path), content_type=mimetypes.guess_type(path)[0] or 'application/octet-stream')

        context.route('**/*', route_handler)
        context.add_init_script('window.__ga=[];window.__meta=[];window.gtag=(...a)=>window.__ga.push(a);window.fbq=(...a)=>window.__meta.push(a);')
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(ORIGIN + '/blog/' + post['slug'], wait_until='load')
        page.wait_for_function('Boolean(window.commandAnalytics)')
        page.wait_for_timeout(120)
        events = page.evaluate('window.__ga.filter(e=>e[0]==="event")')
        viewed = [e for e in events if e[1] == 'view_blog_article']
        assert len(viewed) == 1
        assert viewed[0][2]['article_slug'] == post['slug']
        assert viewed[0][2]['content_id'] == post['slug']
        assert viewed[0][2]['series_order'] == post['series_order']
        # Prevent only the destination action, after production analytics listeners.
        # No real external bookstore page or purchase is opened.
        page.evaluate('document.addEventListener("click",e=>{if(e.target.closest("a[data-cta=purchase]"))e.preventDefault()})')
        available_locations = []
        for location in ('inline', 'end'):
            selector = f'.article-cta-{location} a[data-cta-id="{location}-book"]'
            locator = page.locator(selector)
            if not locator.count():
                assert location == 'inline', f'Missing required end CTA: {post["slug"]}'
                continue
            available_locations.append(location)
            locator.scroll_into_view_if_needed()
            page.wait_for_timeout(1200)
            locator.click()
            page.wait_for_timeout(100)
        google = page.evaluate('window.__ga.filter(e=>e[0]==="event")')
        facebook = page.evaluate('window.__meta.filter(e=>e[0]==="trackCustom")')
        assert len(google) == len(facebook)
        for ga, meta in zip(google, facebook):
            assert ga[1:3] == meta[1:3]
            assert meta[3] == {'eventID': ga[2]['event_id']}
            assert ga[2]['content_id'] == post['slug'] and ga[2]['article_slug'] == post['slug']
            assert ga[2]['series_order'] == post['series_order']
        for event in ('view_conversion_cta', 'click_book_purchase'):
            ids = {e[2]['cta_id'] for e in google if e[1] == event}
            required_ids = {f'{location}-book' for location in available_locations}
            assert required_ids <= ids, (post['slug'], event, ids, required_ids)
        assert not {'lead_form_success', 'purchase', 'generate_lead'} & {e[1] for e in google}
        nav_links = page.locator('.series-nav a[href^="/blog/"]:not([aria-current="page"])')
        if nav_links.count():
            href = nav_links.first.get_attribute('href')
            nav_links.first.click()
            page.wait_for_url(ORIGIN + href)
            page.wait_for_timeout(120)
        assert not errors, errors
        unexpected = [url for url in outside if urlsplit(url).hostname not in ('www.googletagmanager.com', 'googletagmanager.com', 'connect.facebook.net')]
        assert not unexpected, unexpected
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
        context.close()
        print(f'PASS {post["slug"]}: identical GA4/Meta article/series context, visible CTA exposure/click, series navigation, no real purchase or form submission', flush=True)
    browser.close()
print(f'PASS new series offline analytics: {len(POSTS)} published articles, zero live analytics traffic', flush=True)
