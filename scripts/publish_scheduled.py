"""Promote only today's approved article after its Asia/Seoul release time.

This stages local source files only. It never commits, pushes, changes accounts,
contacts analytics, or deploys. The authorized scheduled agent handles checks,
GitHub PR/main integration and verification of the existing Vercel deployment.
Run: python3 scripts/publish_scheduled.py [--dry-run]
Clock injection is available only to tests in a separate workspace.
"""
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
KST = ZoneInfo('Asia/Seoul')
SCHEDULE_PATH = Path('content/scheduled/command-marketing-os')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.scheduled-tmp')
    temporary.write_bytes(data)
    os.replace(temporary, path)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def stage_today(workspace, *, now=None, dry_run=False):
    root = Path(workspace).resolve()
    if now is not None and root == ROOT:
        raise ValueError('An injected clock must never stage the real working repository.')
    clock = now if now is not None else datetime.now(KST)
    if clock.tzinfo is None:
        raise ValueError('Use a timezone-aware timestamp.')
    clock = clock.astimezone(KST)
    directory = root / SCHEDULE_PATH
    schedule = read_json(directory / 'posts.json')
    proof = read_json(directory / 'publication-proof.json')
    assert proof['timezone'] == 'Asia/Seoul'
    assert len({p['slug'] for p in schedule}) == len(schedule)
    assert [p['series_order'] for p in schedule] == list(range(1, len(schedule) + 1))
    published = read_json(root / 'content/blog/posts.json')
    published_by_slug = {p['slug']: p for p in published}
    assert len(published_by_slug) == len(published)
    slots = []
    for post in schedule:
        assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', post['slug'])
        release = datetime.fromisoformat(post['publish_at'])
        assert release.tzinfo and release.utcoffset() == KST.utcoffset(release)
        assert release.astimezone(KST).date().isoformat() == post['date']
        assert post['series_key'] == 'command-marketing-os'
        slots.append((release, post))
    assert [release for release, _ in slots] == sorted(release for release, _ in slots)
    matches = [(release, post) for release, post in slots if release.date() == clock.date()]
    assert len(matches) <= 1, 'Only one article may be scheduled per day.'
    if not matches:
        return {'status': 'no_slot_today', 'local_time': clock.isoformat(), 'changed': False}
    release, post = matches[0]
    slug = post['slug']
    if clock < release:
        return {'status': 'waiting', 'slug': slug, 'publish_at': post['publish_at'], 'changed': False}
    if slug in published_by_slug:
        current = published_by_slug[slug]
        assert {k: v for k, v in current.items() if k != 'modified'} == {k: v for k, v in post.items() if k != 'modified'}, 'Registered article differs from approved metadata.'
        assert post['date'] <= current.get('modified', current['date']) <= clock.date().isoformat()
        registered_files = [(directory / f'{slug}.md', root / 'content/blog' / f'{slug}.md')]
        registered_files += [(directory / 'assets' / Path(post[key]).name, root / 'dist' / post[key].lstrip('/')) for key in ('image', 'image_jpg')]
        for source, target in registered_files:
            relative = source.relative_to(directory).as_posix()
            if not target.is_file() or digest(source) != proof['sha256'][relative] or digest(target) != proof['sha256'][relative]:
                raise ValueError('Incomplete or conflicting registered article files; recover before deployment.')
        assert digest(directory / 'posts.json') == proof['metadata_sha256'], 'Approved metadata changed.'
        registered_catalog = read_json(root / 'content/analytics-events.json')
        registered_site = read_json(root / 'content/site.json')
        if set(registered_catalog['article_slugs']) != set(published_by_slug) or len(registered_catalog['article_slugs']) != len(published_by_slug):
            raise ValueError('Incomplete registration: analytics slugs differ; recover before deployment.')
        if any(registered_site[key] < post['date'] for key in ('home_modified', 'llms_reviewed')):
            raise ValueError('Incomplete registration: site review dates are stale; recover before deployment.')
        return {'status': 'already_registered', 'slug': slug, 'changed': False}
    missing_previous = [p['slug'] for at, p in slots if at < release and p['slug'] not in published_by_slug]
    if missing_previous:
        raise ValueError(f'Previous articles are not published; stop rather than create broken links: {missing_previous}')
    assert set(post['related']) <= set(published_by_slug), 'Related article is not published.'
    files = [(directory / f'{slug}.md', root / 'content/blog' / f'{slug}.md')]
    manuscript = files[0][0].read_text(encoding='utf-8')
    assert manuscript.splitlines()[0] == '# ' + post['title']
    for key in ('image', 'image_jpg'):
        target = Path(post[key].lstrip('/'))
        assert target.parts[:2] == ('assets', 'blog')
        assert target.name in (f'{slug}.webp', f'{slug}.jpg')
        files.append((directory / 'assets' / target.name, root / 'dist' / target))
    for source, target in files:
        relative = source.relative_to(directory).as_posix()
        assert digest(source) == proof['sha256'][relative], f'Approved file changed: {relative}'
        if target.exists():
            assert target.read_bytes() == source.read_bytes(), f'Refuse to overwrite conflicting staged file: {target}'
    assert digest(directory / 'posts.json') == proof['metadata_sha256'], 'Approved metadata changed.'
    catalog = read_json(root / 'content/analytics-events.json')
    assert set(catalog['article_slugs']) == set(published_by_slug)
    site = read_json(root / 'content/site.json')
    if dry_run:
        return {'status': 'ready', 'slug': slug, 'publish_at': post['publish_at'], 'changed': False}
    # Copy assets/source before registering the article; partial staging is safe
    # to retry because exact matching files are accepted and conflicts fail closed.
    for source, target in files:
        if not target.exists():
            write_atomic(target, source.read_bytes())
    for previous in published:
        if previous.get('series_key') == post['series_key']:
            previous['modified'] = max(previous.get('modified', previous['date']), post['date'])
    published.insert(0, deepcopy(post))
    catalog['article_slugs'].append(slug)
    site['home_modified'] = max(site['home_modified'], post['date'])
    site['llms_reviewed'] = max(site['llms_reviewed'], post['date'])
    # Registration files are atomically replaced individually. Tests/build must
    # pass before any Git commit, so a failed transaction cannot be deployed.
    write_atomic(root / 'content/blog/posts.json', json_bytes(published))
    write_atomic(root / 'content/analytics-events.json', json_bytes(catalog))
    write_atomic(root / 'content/site.json', json_bytes(site))
    return {'status': 'staged', 'slug': slug, 'publish_at': post['publish_at'], 'changed': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    print(json.dumps(stage_today(ROOT, dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
