"""Pure article-CTA placement/validation. No build, network or analytics side effects."""
import re
from bs4 import BeautifulSoup

PRACTICAL_HEADING = re.compile(r'예시|예제|실무\s*예|적용해\s*보기|적용\s*예|실행\s*체크|체크리스트|점검표')
REFERENCE_HEADING = re.compile(r'^(?:\d+[.)]\s*)?(?:출처|참고\s*(?:자료|문헌)|references?\b)', re.I)
MIN_REMAINING_TEXT = 160


def normalized_text(node):
    return ' '.join(node.get_text(' ', strip=True).split())


def remaining_body_text(following):
    remaining = []
    for node in [following, *following.find_next_siblings()]:
        if 'article-cta' in node.get('class', []) or (node.name == 'h2' and REFERENCE_HEADING.search(normalized_text(node))):
            break
        remaining.append(normalized_text(node))
    return ' '.join(remaining)


def insert_inline_cta(rendered, cta_markup):
    """Add at most one mid-article CTA; never fall back to the article tail.

    Only practical body headings with a following readable section qualify.
    References do not count as separation from the mandatory end CTA.
    A second call is a no-op, including when the fragment already has an end CTA.
    """
    if rendered.select_one('.article-cta'):
        return False
    candidates = [h for h in rendered.find_all('h2', recursive=False)
                  if not REFERENCE_HEADING.search(normalized_text(h))
                  and PRACTICAL_HEADING.search(normalized_text(h))]
    for anchor in candidates:
        following = anchor.find_next_sibling('h2')
        if not following or REFERENCE_HEADING.search(normalized_text(following)):
            continue
        if len(remaining_body_text(following)) < MIN_REMAINING_TEXT:
            continue
        markup = BeautifulSoup(cta_markup, 'html.parser')
        ctas = markup.select('section.article-cta-inline')
        if len(ctas) != 1:
            raise ValueError('Inline CTA markup must contain exactly one inline section.')
        following.insert_before(ctas[0])
        return True
    return False


def validate_cta_layout(body):
    """Fail a build on duplicate or tail-adjacent CTA panels, not in production."""
    if body is None:
        raise ValueError('Article body is required.')
    ctas = body.select('.article-cta')
    inline = body.select('.article-cta-inline')
    end = body.select('.article-cta-end')
    if len(inline) > 1 or len(end) != 1 or len(ctas) != len(inline) + 1:
        raise ValueError('Require one end CTA and at most one inline CTA.')
    if body.find_all(recursive=False)[-1] is not end[0]:
        raise ValueError('End CTA must be the last article-body element.')
    headings = []
    copies = []
    for cta in ctas:
        heading = cta.find('h3')
        copy = next((p for p in cta.find_all('p', recursive=False)
                     if 'eyebrow' not in p.get('class', [])), None)
        if not heading or not copy:
            raise ValueError('Each CTA needs its own heading and explanatory copy.')
        headings.append(normalized_text(heading))
        copies.append(normalized_text(copy))
        if cta.find_next_sibling() in ctas:
            raise ValueError('Adjacent CTA panels are not allowed.')
    if len(set(headings)) != len(headings) or len(set(copies)) != len(copies):
        raise ValueError('Inline/end CTA headings and copy must be distinct.')
    if inline:
        next_heading = inline[0].find_next_sibling('h2')
        if not next_heading or REFERENCE_HEADING.search(normalized_text(next_heading)):
            raise ValueError('Inline CTA must be followed by a readable body section.')
        if len(remaining_body_text(next_heading)) < MIN_REMAINING_TEXT:
            raise ValueError('Inline CTA needs enough body content before the end CTA.')
