"""Check scheduled releases in a temporary copy, never publish ahead of time.
Run: python3 scripts/check_scheduled.py [--full]
--full also executes the existing analytics/funnel/lead offline checks after
all three articles have been promoted in the copy. External traffic is blocked.
"""
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import json
import shutil
import subprocess
import sys
from bs4 import BeautifulSoup
from publish_scheduled import ROOT, SCHEDULE_PATH, stage_today


def snapshot(path):
    return {p.relative_to(path).as_posix(): sha256(p.read_bytes()).hexdigest()
            for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def execute(workspace, script):
    subprocess.run([sys.executable, str(workspace / 'scripts' / script)], cwd=workspace, check=True)


def timestamp(value):
    return datetime.fromisoformat(value + '+09:00')


def check(full=False):
    schedule = json.loads((ROOT / SCHEDULE_PATH / 'posts.json').read_text())
    planned = {p['slug'] for p in schedule}
    original_posts = json.loads((ROOT / 'content/blog/posts.json').read_text())
    registered = {p['slug'] for p in original_posts}
    assert not (planned & registered), 'Initial preparation must not publish a future article.'
    for slug in planned:
        assert not (ROOT / 'content/blog' / (slug + '.md')).exists()
        assert not (ROOT / 'dist/blog' / slug).exists()
        assert not list((ROOT / 'dist/assets/blog').glob(slug + '.*'))
        for name in ('sitemap.xml', 'llms.txt', 'manus-routes.json'):
            assert slug not in (ROOT / 'dist' / name).read_text()
    real_before = snapshot(ROOT / 'dist')
    try:
        stage_today(ROOT, now=timestamp('2026-10-20T09:00:00'))
        raise AssertionError('Real repository accepted an injected future clock.')
    except ValueError as error:
        assert 'injected clock' in str(error)
    with TemporaryDirectory(prefix='command-series-test-') as temporary:
        work = Path(temporary)
        for directory in ('content', 'scripts', 'dist', 'api', 'apps-script'):
            shutil.copytree(ROOT / directory, work / directory, ignore=shutil.ignore_patterns('__pycache__'))
        before = snapshot(work)
        result = stage_today(work, now=timestamp('2026-10-19T23:59:59'))
        assert result['status'] == 'no_slot_today' and snapshot(work) == before
        result = stage_today(work, now=timestamp('2026-10-20T08:59:59'))
        assert result['status'] == 'waiting' and snapshot(work) == before
        result = stage_today(work, now=timestamp('2026-10-20T09:00:00'), dry_run=True)
        assert result['status'] == 'ready' and snapshot(work) == before
        try:
            stage_today(work, now=timestamp('2026-10-21T09:00:00'))
            raise AssertionError('Missing previous article was accepted.')
        except ValueError as error:
            assert 'Previous articles' in str(error)
        print('PASS before-date/time embargo, dry-run, real-repository clock guard and previous-article dependency', flush=True)
        for index, item in enumerate(schedule):
            result = stage_today(work, now=datetime.fromisoformat(item['publish_at']))
            assert result['status'] == 'staged' and result['slug'] == item['slug']
            after = snapshot(work)
            assert stage_today(work, now=datetime.fromisoformat(item['publish_at']))['status'] == 'already_registered'
            assert snapshot(work) == after
            if index == 0:
                catalog_path = work / 'content/analytics-events.json'
                catalog = json.loads(catalog_path.read_text())
                catalog['article_slugs'].remove(item['slug'])
                site_path = work / 'content/site.json'
                site = json.loads(site_path.read_text())
                site['home_modified'] = '2026-10-19'
                cases = [
                    (catalog_path, json.dumps(catalog).encode()),
                    (site_path, json.dumps(site).encode()),
                    (work / 'dist' / item['image'].lstrip('/'), b'interrupted asset copy'),
                ]
                for broken_path, corrupted in cases:
                    original = broken_path.read_bytes()
                    broken_path.write_bytes(corrupted)
                    broken_before = snapshot(work)
                    try:
                        stage_today(work, now=datetime.fromisoformat(item['publish_at']))
                        raise AssertionError('Partial registration was misreported as success.')
                    except ValueError as error:
                        assert 'registration' in str(error) or 'registered article files' in str(error), str(error)
                    assert snapshot(work) == broken_before, 'Broken-state inspection must not mutate files.'
                    broken_path.write_bytes(original)
                assert snapshot(work) == after
                print('PASS interrupted registration fails closed: analytics slug, site date and corrupt asset; read-only retry', flush=True)
            execute(work, 'build_blog.py')
            built = snapshot(work / 'dist')
            execute(work, 'build_blog.py')
            assert snapshot(work / 'dist') == built, 'Repeated build changed generated content.'
            execute(work, 'check_blog.py')
            execute(work, 'check_cta.py')
            published = json.loads((work / 'content/blog/posts.json').read_text())
            current = {p['slug'] for p in published}
            expected = {p['slug'] for p in schedule[:index + 1]}
            assert current == registered | expected
            catalog = json.loads((work / 'content/analytics-events.json').read_text())
            assert set(catalog['article_slugs']) == current
            for member in schedule:
                slug = member['slug']
                page = work / 'dist/blog' / slug / 'index.html'
                if slug not in expected:
                    assert not page.exists()
                    assert not list((work / 'dist/assets/blog').glob(slug + '.*'))
                    for name in ('sitemap.xml', 'llms.txt', 'manus-routes.json'):
                        assert slug not in (work / 'dist' / name).read_text()
                    continue
                dom = BeautifulSoup(page.read_text(), 'html.parser')
                nav = dom.select_one('.series-nav')
                assert nav and nav['aria-label'] == '커맨드 마케팅 OS 연결 시리즈'
                assert len(nav.select('ol li')) == len(schedule)
                assert len(nav.select('ol a')) == len(expected)
                assert len(nav.select('ol .series-pending')) == len(schedule) - len(expected)
                assert len(nav.select('[aria-current="page"]')) == 1
                assert {a['href'].removeprefix('/blog/') for a in nav.select('a[href^="/blog/"]')} <= expected
                for location in ('inline', 'end'):
                    assert len(dom.select(f'.article-cta-{location}')) == 1
                    purchase = dom.select_one(f'.article-cta-{location} a[data-cta-id="{location}-book"]')
                    assert purchase.get_text() == '책을 통해서 확인해보세요'
                    assert purchase['href'].startswith('https://product.kyobobook.co.kr/detail/S000221439823')
                assert dom.body['data-series-order'] == str(member['series_order'])
                assert dom.body['data-content-group'] == 'practical_guide'
                assert dom.select_one('.article-mobile-cta a')['data-cta-id'] == 'mobile-book'
                graph = json.loads(dom.select_one('script[type="application/ld+json"]').string)['@graph']
                faq = next(node for node in graph if node['@type'] == 'FAQPage')['mainEntity']
                heading = next(h for h in dom.select('.article-body h2') if h.get_text() == '자주 묻는 질문')
                visible = []
                for node in heading.find_next_siblings():
                    if node.name == 'h2':
                        break
                    if node.name == 'h3':
                        visible.append((node.get_text(' ', strip=True), node.find_next_sibling('p').get_text(' ', strip=True)))
                assert visible == [(q['name'], q['acceptedAnswer']['text']) for q in faq]
                assert len(faq) == 4
                post = next(p for p in published if p['slug'] == slug)
                assert post['date'] == member['date'] and post['modified'] == item['date']
            print(f'PASS {item["date"]}: exactly one new article, repeat no-op, navigation/embargo/FAQ/CTA/search/analytics and original publication-date preservation', flush=True)
        execute(work, 'check_series_analytics.py')
        if full:
            for script in ('check_analytics.py', 'check_funnel.py'):
                execute(work, script)
            subprocess.run(['node', str(work / 'scripts/check_lead_backend.cjs')], cwd=work, check=True)
        final = snapshot(work)
        assert stage_today(work, now=timestamp('2026-10-23T09:00:00'))['status'] == 'no_slot_today'
        assert snapshot(work) == final
    assert snapshot(ROOT / 'dist') == real_before, 'Test altered production output.'
    print('PASS scheduled preparation: 3 releases in isolated copy, no real publication or live analytics traffic', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', action='store_true')
    check(parser.parse_args().full)
