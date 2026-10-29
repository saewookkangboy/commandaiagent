"""Read-only production verification; no scripts, events, submissions or purchases.
Run after GitHub main merge: python3 scripts/verify_scheduled_production.py [--schedule-dir content/scheduled/command-marketing-os]
A finite retry is allowed for Vercel propagation, not for future unattended work.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from zoneinfo import ZoneInfo
import argparse
import json
import time

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://book.allrounder.im'
DEFAULT_SCHEDULE_DIR = Path('content/scheduled/command-marketing-os')


def fetch(path, agent='CommandMarketing-ReleaseVerifier/1.0'):
    request = Request(ORIGIN + path, headers={'User-Agent': agent, 'Cache-Control': 'no-cache'})
    try:
        with urlopen(request, timeout=25) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()


def verify(schedule_dir=DEFAULT_SCHEDULE_DIR):
    schedule_path = ROOT / schedule_dir / 'posts.json'
    scheduled = json.loads(schedule_path.read_text())
    posts = json.loads((ROOT / 'content/blog/posts.json').read_text())
    live_slugs = {post['slug'] for post in posts}
    published = [p for p in scheduled if p['slug'] in live_slugs]
    pending = [p for p in scheduled if p['slug'] not in live_slugs]
    paths = {'/': ROOT / 'dist/index.html', '/blog': ROOT / 'dist/blog/index.html',
             '/sitemap.xml': ROOT / 'dist/sitemap.xml', '/llms.txt': ROOT / 'dist/llms.txt',
             '/assets/analytics-config.js': ROOT / 'dist/assets/analytics-config.js'}
    for post in published:
        assert datetime.fromisoformat(post['publish_at']) <= datetime.now(ZoneInfo('Asia/Seoul'))
        paths['/blog/' + post['slug']] = ROOT / 'dist/blog' / post['slug'] / 'index.html'
        for key in ('image', 'image_jpg'):
            paths[post[key]] = ROOT / 'dist' / post[key].lstrip('/')
    results = []

    def compare(item):
        path, local = item
        status, content = fetch(path)
        assert status == 200 and content == local.read_bytes(), f'{path}: status or deployed version differs'
        return {'path': path, 'status': status, 'sha256': sha256(content).hexdigest(), 'matches_main_output': True}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results.extend(pool.map(compare, paths.items()))
    for post in pending:
        status, _ = fetch('/blog/' + post['slug'])
        assert status == 404, f'Pending article is exposed or masked by fallback: {post["slug"]}, {status}'
        for key in ('image', 'image_jpg'):
            status, _ = fetch(post[key])
            assert status == 404, f'Pending asset is exposed: {post[key]}'
    for agent in ('Googlebot', 'Yeti', 'OAI-SearchBot', 'ChatGPT-User', 'Claude-SearchBot', 'Claude-User'):
        for path in ('/sitemap.xml', '/llms.txt', *('/blog/' + p['slug'] for p in published)):
            status, content = fetch(path, agent)
            assert status == 200 and content == paths[path].read_bytes(), (path, agent, status)
    return {'observed_at': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
            'published_series_slugs': [p['slug'] for p in published],
            'pending_series_slugs': [p['slug'] for p in pending],
            'files': results, 'search_bots': '6 bot names: HTTP 200 and identical content',
            'pending_routes_and_assets': 'HTTP 404',
            'no_live_analytics_or_form_submission': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait-seconds', type=int, default=0)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--schedule-dir', type=Path, default=DEFAULT_SCHEDULE_DIR)
    args = parser.parse_args()
    assert 0 <= args.wait_seconds <= 900
    deadline = time.monotonic() + args.wait_seconds
    while True:
        try:
            result = verify(args.schedule_dir)
            break
        except (AssertionError, OSError) as error:
            if time.monotonic() >= deadline:
                raise
            print(f'Waiting for the merged output to reach production: {error}', flush=True)
            time.sleep(15)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
