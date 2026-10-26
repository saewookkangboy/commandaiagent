"""Shared, deterministic topic grouping for the home, blog index and llms.txt."""
from datetime import date
import json
import re


def load_sections(path, posts):
    sections = json.loads(path.read_text())
    assert isinstance(sections, list) and sections, 'Blog sections must be a nonempty list.'
    by_slug = {post['slug']: post for post in posts}
    assert len(by_slug) == len(posts), 'Duplicate post slugs.'
    ids, titles, assigned, result = set(), set(), [], []
    for section in sections:
        identifier = section['id']
        assert re.fullmatch(r'[a-z][a-z0-9-]{0,79}', identifier), identifier
        assert identifier not in ids and identifier != 'practical-guides', 'Duplicate or reserved section ID.'
        ids.add(identifier)
        for key in ('title', 'eyebrow', 'description'):
            assert isinstance(section[key], str) and section[key] == section[key].strip() and section[key], (identifier, key)
        assert section['title'] not in titles, 'Duplicate section titles.'
        titles.add(section['title'])
        slugs = section['slugs']
        assert isinstance(slugs, list) and slugs, (identifier, 'No classified posts.')
        assert all(slug in by_slug for slug in slugs), (identifier, 'Unpublished or unknown article.')
        assigned.extend(slugs)
        members = [by_slug[slug] for slug in slugs]
        mode = section['sort']
        assert mode in ('reading', 'series', 'latest'), (identifier, mode)
        if mode == 'latest':
            members = sorted(members, key=lambda post: (date.fromisoformat(post['date']), post['slug']), reverse=True)
        elif mode == 'series':
            series_key = section['series_key']
            assert all(post.get('series_key') == series_key for post in members), (identifier, 'Mixed series.')
            assert len({post['series_order'] for post in members}) == len(members), (identifier, 'Duplicate series order.')
            members = sorted(members, key=lambda post: post['series_order'])
        result.append({**section, 'posts': members})
    assert len(assigned) == len(set(assigned)), 'An article appears in more than one section.'
    assert set(assigned) == set(by_slug), f'Unclassified articles: {sorted(set(by_slug) - set(assigned))}'
    return result
