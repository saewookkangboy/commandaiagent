"""Optional local regression check. Needs Playwright and a Chromium executable.
Run the preview first: python3 scripts/serve_preview.py --port 4173
Then: python3 scripts/check_browser.py
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json

BASE = 'http://127.0.0.1:4173'
ROOT = Path(__file__).resolve().parents[1]
POSTS = json.loads((ROOT / 'content/blog/posts.json').read_text())

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    errors = []
    requests = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('request', lambda request: requests.append(request.url))
    page.goto(BASE, wait_until='networkidle')
    assert not errors, errors
    assert not any('googletagmanager' in url or 'facebook.com' in url for url in requests), requests
    page.evaluate("window.commandTrackingEnabled=true;window.testEvents=[];window.gtag=(kind,name,args)=>window.testEvents.push({name,args});window.fbq=()=>{}")
    page.locator('[data-diagnosis-start]').click()
    for situation in ('solo', 'team', 'loop'):
        page.locator(f'input[name="situation"][value="{situation}"]').check()
        page.locator('#situation-form button[type="submit"]').click()
        assert page.evaluate('location.hash') == '#situation-' + situation
        assert page.evaluate('document.activeElement.id') == 'situation-' + situation
    for situation, parts in [('solo', [3,5,7]), ('team', [2,3,7]), ('loop', [4,5,6])]:
        page.locator('[data-reading-path="' + situation + '"]').click()
        for number in parts:
            assert page.locator('#part-' + str(number)).evaluate('(node)=>node.open')
    page.locator('[data-rgctor="Review"] summary').click()
    assert page.locator('[data-rgctor="Review"]').evaluate('(node)=>node.open')
    page.locator('#day1-preview summary').click()
    assert page.locator('#day1-preview').evaluate('(node)=>node.open')
    page.wait_for_timeout(100)
    before = page.evaluate('window.testEvents.length')
    for checkbox in page.locator('#day1-preview input[type="checkbox"]').all():
        checkbox.check()
    page.wait_for_timeout(100)
    after_events = page.evaluate('window.testEvents.slice(' + str(before) + ')')
    assert not after_events, after_events
    assert page.evaluate('localStorage.length') == 0
    assert page.evaluate('sessionStorage.length') == 0
    names = page.evaluate('window.testEvents.map(e=>e.name)')
    assert names.count('start_situation_diagnosis') == 1
    assert names.count('select_solo_team_loop') == 3
    assert 'open_rgctor_example' in names and 'open_day1_preview' in names, names
    print('Interaction and event checks passed:', sorted(set(names)))
    for width in (390, 768, 1061, 1440):
        page.set_viewport_size({'width':width, 'height':844})
        for path in ['/', '/blog', '/blog/technical-seo-ai-search']:
            page.goto(BASE+path, wait_until='networkidle')
            overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth')
            assert not overflow, (width,path,'document overflow')
            bad_header = page.evaluate("Array.from(document.querySelectorAll('.site-head a,.site-head summary')).filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.right>innerWidth+1||r.left< -1)}).map(e=>e.textContent)")
            assert not bad_header, (width,path,bad_header)
        print('Responsive checks passed:', width)
    for post in POSTS:
        page.goto(BASE+'/blog/'+post['slug'], wait_until='networkidle')
        assert page.locator('h1').inner_text()==post['title']
        assert page.locator('.article-body').inner_text().__len__()>1800
    page.goto(BASE+'/missing-page-example')
    assert '이 페이지는 찾을 수 없습니다.' in page.locator('h1').inner_text()
    no_js = browser.new_context(java_script_enabled=False)
    no_js_page = no_js.new_page()
    no_js_page.goto(BASE)
    assert no_js_page.locator('#practice').count()==1
    assert no_js_page.locator('#quickstart h2').is_visible()
    no_js_page.goto(BASE+'/blog/'+POSTS[0]['slug'])
    assert no_js_page.locator('.article-body').is_visible()
    assert not errors, errors
    print('5 articles, missing route, no-JS content and zero runtime errors checked.')
    browser.close()
