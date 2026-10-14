"""Offline funnel tests. Every production URL is fulfilled locally; no real lead/analytics traffic."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
import json
import mimetypes

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
ORIGIN = 'https://book.allrounder.im'
CATALOG = json.loads((ROOT / 'content/analytics-events.json').read_text())

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])

    def setup(path, *, width=390, approved=True, configured=True):
        context = browser.new_context(viewport={'width':width,'height':844})
        sent, errors, outside = [], [], []
        mode = {'value':'success'}
        def route_handler(route):
            request = route.request
            url = urlsplit(request.url)
            if url.hostname != 'book.allrounder.im':
                outside.append(request.url); route.abort(); return
            if url.path == '/api/lead':
                if request.method == 'GET':
                    route.fulfill(json={'configured':configured,'version':'2026-10-14-v1'}); return
                data = request.post_data_json; sent.append(data)
                if mode['value'] == 'network': route.abort(); return
                if mode['value'] == 'server': route.fulfill(status=502,json={'ok':False,'error':'unavailable'}); return
                if mode['value'] == 'rate': route.fulfill(status=429,json={'ok':False,'error':'rate_limited'}); return
                route.fulfill(json={'ok':True,'duplicate':len(sent)>1}); return
            local = DIST / unquote(url.path).lstrip('/')
            if local.is_dir(): local = local / 'index.html'
            if not local.is_file(): route.fulfill(status=404,path=str(DIST/'404.html'),content_type='text/html'); return
            if local.suffix == '.html':
                text = local.read_text()
                if not approved: text=text.replace('data-policy-approved="true"','data-policy-approved="false"')
                route.fulfill(body=text,content_type='text/html'); return
            route.fulfill(path=str(local),content_type=mimetypes.guess_type(local)[0] or 'application/octet-stream')
        context.route('**/*',route_handler)
        context.add_init_script('window.__ga=[];window.__meta=[];window.gtag=(...args)=>window.__ga.push(args);window.fbq=(...args)=>window.__meta.push(args);')
        page=context.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(ORIGIN+path,wait_until='load');page.wait_for_timeout(100)
        return context,page,sent,mode,errors,outside

    for approved,configured in [(False,True),(True,False)]:
        context,page,sent,mode,errors,outside=setup('/consulting',approved=approved,configured=configured)
        assert page.locator('#consulting-form').is_hidden()
        assert page.locator('#form-unavailable').is_visible()
        assert not sent and not errors
        context.close()
    print('PASS policy and backend configuration fail closed with real email fallback',flush=True)

    context,page,sent,mode,errors,outside=setup('/consulting?from=rgctor-content-workflow&work=review&intent=workflow&cta=end-team&email=do-not-prefill%40example.invalid')
    page.locator('#consulting-form').wait_for(state='visible')
    assert page.locator('#email').input_value()==''
    assert page.locator('#work_area').input_value()=='review'
    assert page.locator('#inquiry_type').input_value()=='workflow'
    page.locator('#consulting-form button[type=submit]').click()
    assert page.locator('#error-email').inner_text()
    assert page.locator('#email').evaluate('e=>e===document.activeElement')
    assert not sent and page.locator('#form-success').is_hidden()
    page.locator('#email').fill('private-marker@example.invalid')
    page.locator('#consulting-form details summary').click()
    page.locator('#organization').fill('private-org-marker')
    page.locator('#message').fill('private-message-marker')
    page.locator('#consent').check()
    mode['value']='server';page.locator('#consulting-form button[type=submit]').click()
    page.wait_for_function('document.getElementById("form-status").textContent.includes("保存")||document.getElementById("form-status").textContent.includes("입력 내용은 유지")')
    assert page.locator('#form-success').is_hidden() and len(sent)==1
    assert page.locator('#email').input_value()=='private-marker@example.invalid'
    mode['value']='network';page.locator('#consulting-form button[type=submit]').click()
    page.wait_for_function('document.getElementById("form-status").textContent.includes("중복 저장")')
    assert len(sent)==2 and sent[0]['submission_id']==sent[1]['submission_id']
    mode['value']='success'
    page.evaluate('document.getElementById("consulting-form").requestSubmit();document.getElementById("consulting-form").requestSubmit();')
    page.locator('#form-success').wait_for(state='visible')
    assert len(sent)==3 and len({row['submission_id'] for row in sent})==1
    assert sent[-1]['source_article_slug']=='rgctor-content-workflow' and sent[-1]['cta_id']=='end-team'
    assert page.locator('#consulting-form').is_hidden()
    assert page.locator('#form-success').evaluate('e=>e===document.activeElement')
    ga=page.evaluate('window.__ga.filter(e=>e[0]==="event")')
    meta=page.evaluate('window.__meta.filter(e=>e[0]==="trackCustom")')
    assert len(ga)==len(meta)
    for google,facebook in zip(ga,meta):
        assert google[1:3]==facebook[1:3]
        assert facebook[3]['eventID']==google[2]['event_id']
    assert [event[1] for event in ga].count('lead_form_start')==1
    assert [event[1] for event in ga].count('lead_form_success')==1
    assert [event[1] for event in ga].count('lead_form_error')==3
    assert all(row[2].get('source_article_slug')=='rgctor-content-workflow' for row in ga)
    assert not any(value in json.dumps(ga) for value in ['private-marker','private-org-marker','private-message-marker','do-not-prefill'])
    assert page.evaluate('localStorage.length+sessionStorage.length')==0
    assert not errors,errors
    context.close()
    print('PASS form prefill allowlist, accessible errors, preserved retry values/ID, double-submit guard, save-only success and identical private-data-free analytics',flush=True)

    context,page,sent,mode,errors,outside=setup('/blog/rgctor-content-workflow')
    bar=page.locator('.article-mobile-cta')
    assert bar.is_hidden()
    page.locator('.article-body h2').nth(2).scroll_into_view_if_needed();page.wait_for_timeout(200)
    if bar.is_hidden():
        page.locator('.article-body h2').nth(3).scroll_into_view_if_needed();page.wait_for_timeout(200)
    assert bar.is_visible()
    page.wait_for_timeout(1200)
    exposure=page.evaluate('window.__ga.filter(e=>e[0]==="event"&&e[1]==="view_conversion_cta")')
    assert any(row[2]['cta_id']=='mobile-team' for row in exposure)
    page.locator('.article-cta-inline').scroll_into_view_if_needed();page.wait_for_timeout(150)
    assert bar.is_hidden(),'Sticky bar overlaps body CTA'
    page.locator('.article-body h2').nth(3).scroll_into_view_if_needed();page.wait_for_timeout(150)
    if bar.is_hidden():page.locator('.article-body h2').nth(4).scroll_into_view_if_needed();page.wait_for_timeout(150)
    if bar.is_visible():
        page.locator('.article-mobile-cta-close').click()
        assert bar.is_hidden()
        page.mouse.wheel(0,300);page.wait_for_timeout(120)
        assert bar.is_hidden()
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert not errors,errors
    context.close()
    print('PASS delayed mobile CTA exposure, inline exclusion, dismiss and no horizontal overflow',flush=True)

    context,page,sent,mode,errors,outside=setup('/resources/rgctor-worksheet',width=1440)
    page.locator('[data-resource-id="rgctor-worksheet"]').click()
    page.wait_for_timeout(100)
    ga=page.evaluate('window.__ga.filter(e=>e[0]==="event")')
    assert any(e[1]=='resource_access' and e[2]['access_type']=='download' for e in ga)
    assert not any(e[1]=='lead_form_success' for e in ga)
    assert not sent and not errors
    context.close()
    print('PASS real downloadable resource action is not counted as a lead',flush=True)
    browser.close()
