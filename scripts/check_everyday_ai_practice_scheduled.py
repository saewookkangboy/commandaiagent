"""Simulate all five approved practice-series releases in a temporary copy only.

No real site files are registered, no Git state is changed, and browser checks
block external traffic. Run: python3 scripts/check_everyday_ai_practice_scheduled.py [--full]
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
from publish_scheduled import ROOT, stage_today

SCHEDULE_REL = Path('content/scheduled/everyday-ai-practice')


def snapshot(path):
    return {p.relative_to(path).as_posix(): sha256(p.read_bytes()).hexdigest()
            for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def run(workspace, script):
    subprocess.run([sys.executable, str(workspace / 'scripts' / script)], cwd=workspace, check=True)


def at(value):
    return datetime.fromisoformat(value + '+09:00')


def check(full=False):
    schedule_dir = ROOT / SCHEDULE_REL
    schedule = json.loads((schedule_dir / 'posts.json').read_text())
    section_config = json.loads((schedule_dir / 'section.json').read_text())
    planned = [item['slug'] for item in schedule]
    original = json.loads((ROOT / 'content/blog/posts.json').read_text())
    registered = {item['slug'] for item in original}
    assert not (set(planned) & registered), 'Preparation must not expose any practice-series article.'
    baseline = snapshot(ROOT / 'dist')
    for slug in planned:
        assert not (ROOT / 'content/blog' / f'{slug}.md').exists()
        assert not (ROOT / 'dist/blog' / slug).exists()
        assert not list((ROOT / 'dist/assets/blog').glob(slug + '.*'))
        for name in ('sitemap.xml', 'llms.txt', 'manus-routes.json'):
            assert slug not in (ROOT / 'dist' / name).read_text()

    with TemporaryDirectory(prefix='everyday-ai-practice-test-') as temporary:
        work = Path(temporary)
        for directory in ('content', 'scripts', 'dist', 'api', 'apps-script'):
            shutil.copytree(ROOT / directory, work / directory, ignore=shutil.ignore_patterns('__pycache__'))
        before = snapshot(work)
        result = stage_today(work, now=at('2026-10-29T08:59:59'), schedule_dir=SCHEDULE_REL)
        assert result['status'] == 'waiting' and snapshot(work) == before
        result = stage_today(work, now=at('2026-10-29T09:00:00'), dry_run=True, schedule_dir=SCHEDULE_REL)
        assert result['status'] == 'ready' and snapshot(work) == before
        try:
            stage_today(work, now=at('2026-10-30T09:00:00'), schedule_dir=SCHEDULE_REL)
            raise AssertionError('A later post published before its predecessor.')
        except ValueError as error:
            assert 'Previous articles' in str(error)
        print('PASS embargo, dry-run and previous-article dependency', flush=True)

        for index, item in enumerate(schedule):
            now = datetime.fromisoformat(item['publish_at'])
            result = stage_today(work, now=now, schedule_dir=SCHEDULE_REL)
            assert result['status'] == 'staged' and result['slug'] == item['slug']
            after = snapshot(work)
            assert stage_today(work, now=now, schedule_dir=SCHEDULE_REL)['status'] == 'already_registered'
            assert snapshot(work) == after, 'An idempotent retry changed files.'

            if item['date'] in ('2026-10-31', '2026-11-01'):
                raise AssertionError('Non-release dates must never appear in the manifest.')
            run(work, 'build_blog.py')
            built = snapshot(work / 'dist')
            run(work, 'build_blog.py')
            assert snapshot(work / 'dist') == built, 'Repeated build changed output.'
            run(work, 'check_blog.py')
            run(work, 'check_cta.py')
            published = json.loads((work / 'content/blog/posts.json').read_text())
            current = {post['slug'] for post in published}
            expected = set(planned[:index + 1])
            assert current == registered | expected
            public_sections = json.loads((work / 'content/blog/sections.json').read_text())
            active = next(section for section in public_sections if section['id'] == section_config['id'])
            assert active['slugs'] == planned[:index + 1]
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
                assert nav and nav['aria-label'] == member['series_title']
                assert len(nav.select('ol li')) == 5
                assert len(nav.select('ol a')) == index + 1
                assert len(nav.select('ol .series-pending')) == 4 - index
                assert len(nav.select('[aria-current="page"]')) == 1
                assert {a['href'].removeprefix('/blog/') for a in nav.select('a[href^="/blog/"]')} <= expected
                assert dom.body['data-series-order'] == str(member['series_order'])
                assert dom.body['data-content-group'] == 'practical_guide'
                faq = next(node for node in json.loads(dom.select_one('script[type="application/ld+json"]').string)['@graph'] if node['@type'] == 'FAQPage')['mainEntity']
                heading = next(node for node in dom.select('.article-body h2') if node.get_text() == '자주 묻는 질문')
                visible = []
                for node in heading.find_next_siblings():
                    if node.name == 'h2':
                        break
                    if node.name == 'h3':
                        visible.append((node.get_text(' ', strip=True), node.find_next_sibling('p').get_text(' ', strip=True)))
                assert visible == [(question['name'], question['acceptedAnswer']['text']) for question in faq]
                assert len(faq) == 2
                assert dom.select_one('.article-head img')['src'] == member['image_jpg']
            run(work, 'check_series_analytics.py')
            print(f"PASS {item['date']}: one scheduled post, next dates hidden, section, series navigation, metadata, FAQ, CTA and analytics", flush=True)

        # Dates without an article slot are an explicit no-op.
        final = snapshot(work)
        for value in ('2026-10-31T09:00:00', '2026-11-01T09:00:00'):
            result = stage_today(work, now=at(value), schedule_dir=SCHEDULE_REL)
            assert result['status'] == 'no_slot_today' and snapshot(work) == final
        run(work, 'check_blog_sections.py')
        if full:
            for script in ('check_analytics.py', 'check_funnel.py'):
                run(work, script)
            subprocess.run(['node', str(work / 'scripts/check_lead_backend.cjs')], cwd=work, check=True)

    assert snapshot(ROOT / 'dist') == baseline, 'Simulation changed production output.'
    print('PASS five-date series simulation: public workspace untouched', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', action='store_true')
    check(parser.parse_args().full)
