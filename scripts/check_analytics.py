"""Offline browser regression tests; all external requests are aborted.
The production hostname is fulfilled from local dist files. No live analytics traffic.
Run: python3 scripts/check_analytics.py
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import mimetypes

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
ORIGIN = 'https://book.allrounder.im'
CATALOG = json.loads((ROOT / 'content/analytics-events.json').read_text())
POSTS = json.loads((ROOT / 'content/blog/posts.json').read_text())
COVERED = set()
BASE_KEYS = {'event_version', 'event_id', 'page_path', 'page_type', 'content_id', 'content_group', 'funnel_stage', 'article_slug', 'series_order', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'ui_variant', 'source_article_slug'}


def check_pairs(records):
    ga = [args for channel, args in records if channel == 'ga' and args[0] == 'event']
    meta = [args for channel, args in records if channel == 'meta' and args[0] == 'trackCustom']
    assert len(ga) == len(meta), (len(ga), len(meta))
    ids = []
    for google, facebook in zip(ga, meta):
        assert google[1:3] == facebook[1:3], (google, facebook)
        name, parameters = google[1:3]
        assert name in CATALOG['events'] and len(name) < 40
        assert facebook[3] == {'eventID': parameters['event_id']}
        assert set(parameters) <= BASE_KEYS | set(CATALOG['events'][name]['parameters']) | set(CATALOG['events'][name].get('optional_parameters',[]))
        assert len(parameters) <= 25
        assert all(not isinstance(v, str) or len(v) <= 100 for v in parameters.values())
        assert parameters['event_version'] == CATALOG['version']
        assert '?' not in parameters['page_path'] and '#' not in parameters['page_path']
        assert not {'purchase', 'generate_lead', 'book_store_click'} & {name}
        ids.append(parameters['event_id'])
        COVERED.add(name)
    assert len(ids) == len(set(ids)), 'An event was duplicated with the same ID'
    return ga


with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])

    def make_page(url=ORIGIN+'/', *, ga_error=False, meta_error=False, disabled=False, queues=False, clock=False):
        context = browser.new_context(viewport={'width':1440,'height':1000})
        records, outside, errors = [], [], []
        context.expose_function('__recordAnalytics', lambda channel, args: records.append((channel,args)))
        def route_handler(route):
            request_url = urlsplit(route.request.url)
            if request_url.hostname not in ('book.allrounder.im', 'localhost', 'preview.example.test'):
                outside.append(route.request.url)
                route.abort()
                return
            path = DIST / unquote(request_url.path).lstrip('/')
            if path.is_dir(): path = path / 'index.html'
            if not path.is_file():
                route.fulfill(status=404, path=str(DIST / '404.html'), content_type='text/html')
                return
            route.fulfill(status=200, path=str(path), content_type=mimetypes.guess_type(path)[0] or 'application/octet-stream')
        context.route('**/*', route_handler)
        context.add_init_script('''window.__ga=[];window.__meta=[];window.__testHidden=false;
Object.defineProperty(document,'hidden',{configurable:true,get:()=>window.__testHidden});
''' + ("window.commandTrackingEnabled=false;\n" if disabled else '') + ('' if queues else f'''
window.gtag=(...args)=>{{if({str(ga_error).lower()})throw new Error('mock GA unavailable');window.__ga.push(args);window.__recordAnalytics('ga',args);}};
window.fbq=(...args)=>{{if({str(meta_error).lower()})throw new Error('mock Meta unavailable');window.__meta.push(args);window.__recordAnalytics('meta',args);}};
'''))
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        if clock: page.clock.install()
        page.goto(url, wait_until='load')
        page.wait_for_function('Boolean(window.commandAnalytics)')
        page.wait_for_timeout(70)
        return context, page, records, outside, errors

    # Static integration is part of the editorial regression: no hidden legacy code.
    for html in DIST.rglob('*.html'):
        dom = BeautifulSoup(html.read_text(),'html.parser')
        assert len(dom.select('script[src="/assets/analytics-config.js"]')) == 1, html
        assert len(dom.select('script[src="/assets/analytics.js"]')) == 1, html
        assert not any("fbq('init'" in tag.get_text() or 'const track=' in tag.get_text() for tag in dom.find_all('script')), html
    assert CATALOG['ga4_id'] == 'G-QK0BMHHNR5' and CATALOG['meta_pixel_id'] == '2327515324662416'

    context, page, records, outside, errors = make_page(ORIGIN+'/?utm_source=naver&utm_medium=organic&utm_campaign=book-oct&email=private%40example.com&utm_content=private%40example.com&subject=private-message')
    assert len(page.evaluate('window.__ga.filter(a=>a[0]==="config")')) == 1
    assert len(page.evaluate('window.__meta.filter(a=>a[0]==="track"&&a[1]==="PageView")')) == 1
    page_view = page.evaluate('window.__meta.find(a=>a[0]==="track"&&a[1]==="PageView")')
    assert len(page_view) == 4 and set(page_view[2]) == {'event_id'}
    assert page_view[3] == {'eventID': page_view[2]['event_id']} and page_view[2]['event_id']
    assert not any(e[0]=='event' and e[1]=='maturity_select' for e in page.evaluate('window.__ga'))
    page.locator('.maturity-btn[aria-selected="true"]').click()
    assert not any(e[0]=='event' and e[1]=='maturity_select' for e in page.evaluate('window.__ga'))
    # Prevent the mail application's default action only after the production listener.
    page.evaluate("document.addEventListener('click',e=>{if(e.target.closest('a[href^=\"mailto:\"]'))e.preventDefault()})")
    page.locator('[data-cta="purchase"][data-position="hero"]').click()
    page.locator('[data-consulting-path][data-position="hero"]').click()
    page.locator('[data-cta="inquiry"][data-position="consulting-scope"]').click()
    page.locator('[data-cta="preview"][data-position="quickstart-team"]').click()
    page.locator('[data-diagnosis-start]').click()
    for situation in ('solo','team','loop'):
        page.locator(f'input[name="situation"][value="{situation}"]').check()
        page.locator('#situation-form button[type="submit"]').click()
        assert page.evaluate('document.activeElement.id') == 'situation-'+situation
    page.locator('[data-reading-path="solo"]').click()
    assert page.locator('#part-3').evaluate('(e)=>e.open')
    page.locator('[data-rgctor="Review"] summary').click()
    page.locator('[data-rgctor="Review"] summary').click()
    page.locator('[data-rgctor="Review"] summary').click()
    page.locator('#day1-preview summary').click()
    page.locator('#day1-preview input').first.evaluate("e=>e.value='private-checkbox@example.com'")
    for checkbox in page.locator('#day1-preview input[type="checkbox"]').all(): checkbox.check()
    page.locator('[data-personal-path]').click()
    page.locator('.faq-card summary').last.click()
    page.locator('.maturity-btn').first.click()
    page.locator('.maturity-btn').first.press('Home')
    page.locator('.maturity-btn').first.press('ArrowDown')
    page.locator('.maturity-btn').first.click()
    maturity = page.evaluate('window.__ga.filter(a=>a[0]==="event"&&a[1]==="maturity_select").map(a=>a[2].level)')
    assert maturity == [1, 2, 1], maturity
    page.locator('.maturity-btn').last.click()
    maturity = page.evaluate('window.__ga.filter(a=>a[0]==="event"&&a[1]==="maturity_select").map(a=>a[2].level)')
    assert maturity == [1, 2, 1, 5], maturity
    page.locator('.maturity-btn').last.press('End')
    assert page.evaluate('window.__ga.filter(a=>a[0]==="event"&&a[1]==="maturity_select").map(a=>a[2].level)') == maturity
    page.evaluate("window.commandAnalytics.emit('inquiry_start',{position:'manual',email:'private@example.com',subject:'private-message',body:'private-body'})")
    assert page.evaluate("window.commandAnalytics.emit('Purchase',{})") is False
    assert page.evaluate("window.commandAnalytics.emit('inquiry_start',{position:'private@example.com'})") is False
    page.add_script_tag(path=str(DIST/'assets/analytics.js'))
    assert len(page.evaluate('window.__ga.filter(a=>a[0]==="config")')) == 1
    assert page.evaluate('window.__meta.filter(a=>a[0]==="track"&&a[1]==="PageView")') == [page_view]
    page.wait_for_timeout(100)
    ga = check_pairs(records)
    names = [event[1] for event in ga]
    for name in ('click_book_purchase','click_consulting_path','preview_open','start_situation_diagnosis','open_rgctor_example','open_day1_preview'):
        assert names.count(name) == 1, (name,names)
    assert names.count('select_solo_team_loop') == 3
    assert names.count('inquiry_start') == 2
    assert 'faq_expand' in names and 'maturity_select' in names and 'section_view' in names and 'scroll_depth' in names
    assert not any(secret in json.dumps(ga) for secret in ('private@example.com','private-message','private-body','private-checkbox'))
    assert all(event[2].get('utm_campaign')=='book-oct' and 'utm_content' not in event[2] for event in ga)
    assert page.evaluate('localStorage.length+sessionStorage.length') == 0
    # Real internal navigation, not a synthetic click followed by a manual goto.
    page.locator('#blog [data-blog-link="book-command-marketer-01"]').first.click()
    page.wait_for_url(ORIGIN+'/blog/book-command-marketer-01')
    page.wait_for_timeout(100)
    ga=check_pairs(records)
    opened=[e[2] for e in ga if e[1]=='open_blog_article']
    assert len(opened)==1 and opened[0]['article_slug']=='book-command-marketer-01'
    assert any(e[1]=='view_blog_article' and e[2]['series_order']==1 for e in ga)
    page.locator('.series-nav a[href="/blog/book-command-marketer-02"]').first.click()
    page.wait_for_url(ORIGIN+'/blog/book-command-marketer-02')
    page.wait_for_timeout(100)
    assert any(e[1]=='open_blog_article' and e[2]['position']=='series-nav' for e in check_pairs(records))
    assert not errors, errors
    context.close()
    print('PASS shared payload, event IDs, single-action routing, privacy allowlist, actual blog/series navigation',flush=True)

    # Hidden time cannot satisfy engagement or completion. A bottom jump alone is insufficient.
    context,page,records,outside,errors=make_page(ORIGIN+'/blog/book-command-marketer-03',clock=True)
    page.locator('#article-end').scroll_into_view_if_needed()
    page.wait_for_timeout(100)
    assert not any(e[1]=='blog_article_complete' for e in check_pairs(records))
    page.evaluate("window.__testHidden=true;document.dispatchEvent(new Event('visibilitychange'))")
    page.clock.run_for(60000)
    assert not any(e[1] in ('engaged_30s','blog_article_complete') for e in check_pairs(records))
    page.evaluate("window.__testHidden=false;document.dispatchEvent(new Event('visibilitychange'))")
    page.clock.run_for(31000)
    page.wait_for_timeout(100)
    names=[e[1] for e in check_pairs(records)]
    assert names.count('engaged_30s')==1 and names.count('blog_article_complete')==1,names
    page.clock.run_for(30000)
    assert [e[1] for e in check_pairs(records)].count('blog_article_complete')==1
    assert not errors,errors
    context.close()

    context,page,records,outside,errors=make_page(ORIGIN+'/blog/technical-seo-ai-search',clock=True)
    page.clock.run_for(10000)
    page.evaluate("window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))")
    page.clock.run_for(60000)
    assert not any(e[1]=='engaged_30s' for e in check_pairs(records))
    page.evaluate("window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))")
    page.clock.run_for(21000)
    page.wait_for_timeout(100)
    assert [e[1] for e in check_pairs(records)].count('engaged_30s')==1
    assert not errors,errors
    context.close()
    print('PASS visible30s, bottom-plus-time completion and BFCache pause/resume',flush=True)

    # An observer entry received while hidden must be remembered, not counted then lost.
    context,page,records,outside,errors=make_page()
    page.evaluate("document.documentElement.style.scrollBehavior='auto';window.__testHidden=true;document.dispatchEvent(new Event('visibilitychange'));document.querySelector('#system h2').scrollIntoView({block:'center'})")
    page.wait_for_timeout(150)
    assert not page.evaluate('window.__ga.some(a=>a[0]==="event"&&a[1]==="section_view"&&a[2].section_name==="system")')
    page.evaluate("window.__testHidden=false;document.dispatchEvent(new Event('visibilitychange'))")
    page.wait_for_timeout(100)
    system_views=page.evaluate('window.__ga.filter(a=>a[0]==="event"&&a[1]==="section_view"&&a[2].section_name==="system")')
    assert len(system_views)==1,system_views
    page.evaluate("document.dispatchEvent(new Event('visibilitychange'));window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))")
    page.wait_for_timeout(100)
    assert len(page.evaluate('window.__ga.filter(a=>a[0]==="event"&&a[1]==="section_view"&&a[2].section_name==="system")'))==1
    check_pairs(records)
    assert not errors,errors
    context.close()

    # Merely intersecting at less than 50% does not qualify as a section view.
    context,page,records,outside,errors=make_page()
    page.evaluate("document.documentElement.style.scrollBehavior='auto';const h=document.querySelector('#system h2');window.scrollTo(0,h.getBoundingClientRect().top+scrollY-innerHeight+h.getBoundingClientRect().height*0.25)")
    page.wait_for_timeout(150)
    assert not page.evaluate('window.__ga.some(a=>a[0]==="event"&&a[1]==="section_view"&&a[2].section_name==="system")')
    page.evaluate("document.querySelector('#system h2').scrollIntoView({block:'center'})")
    page.wait_for_timeout(150)
    assert len(page.evaluate('window.__ga.filter(a=>a[0]==="event"&&a[1]==="section_view"&&a[2].section_name==="system")'))==1
    check_pairs(records)
    assert not errors,errors
    context.close()
    print('PASS PageView eventID, unchanged maturity suppression, visible section recovery and 50% threshold',flush=True)

    for url in ('http://localhost/','https://preview.example.test/blog/book-command-marketer-01',ORIGIN+'/missing-analytics-test'):
        context,page,records,outside,errors=make_page(url)
        page.evaluate('window.commandTrackingEnabled=true')
        assert page.evaluate("window.commandAnalytics.emit('inquiry_start',{position:'manual'})") is False
        assert not records and not outside and not errors,(url,records,outside,errors)
        context.close()
    context,page,records,outside,errors=make_page(disabled=True)
    assert not records and not outside and not errors
    context.close()
    print('PASS localhost/preview/404/pre-disabled SDK and event blocking',flush=True)

    for ga_error,meta_error,expected in ((True,False,'meta'),(False,True,'ga')):
        context,page,records,outside,errors=make_page(ga_error=ga_error,meta_error=meta_error)
        assert page.evaluate("window.commandAnalytics.emit('inquiry_start',{position:'manual'})") is True
        page.wait_for_timeout(70)
        assert any(channel==expected and args[1]=='inquiry_start' for channel,args in records if args[0] in ('event','trackCustom'))
        assert not errors,errors
        context.close()
    context,page,records,outside,errors=make_page(queues=True)
    assert page.evaluate('dataLayer.filter(a=>a[0]==="config").length')==1
    assert page.evaluate('fbq.queue.filter(a=>a[0]==="init").length')==1
    assert page.evaluate('fbq.queue.filter(a=>a[0]==="track"&&a[1]==="PageView").length')==1
    queued_page_view=page.evaluate('Array.from(fbq.queue.find(a=>a[0]==="track"&&a[1]==="PageView"))')
    assert queued_page_view[3] == {'eventID': queued_page_view[2]['event_id']}
    assert any('googletagmanager.com' in url for url in outside) and any('connect.facebook.net' in url for url in outside)
    assert not errors,errors
    context.close()
    print('PASS independent SDK failure handling and native SDK queues',flush=True)

    for post in POSTS:
        context,page,records,outside,errors=make_page(ORIGIN+'/blog/'+post['slug'])
        events=[e for e in check_pairs(records) if e[1]=='view_blog_article']
        assert len(events)==1 and events[0][2]['content_id']==post['slug']
        assert events[0][2]['content_group']==('book_series' if post.get('kind')=='book-series' else 'practical_guide')
        assert not errors,errors
        context.close()
    assert set(CATALOG['events']) - {'view_conversion_cta','lead_form_start','lead_form_error','lead_form_success','resource_access'} <= COVERED, ('Missing legacy coverage',set(CATALOG['events'])-COVERED)
    browser.close()
    print(f'PASS all19 legacy events (new funnel actions have dedicated tests) and all{len(POSTS)} article contexts; zero live analytics traffic',flush=True)
