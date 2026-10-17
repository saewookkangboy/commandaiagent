"""Offline regression checks for non-duplicating article CTA placement."""
from pathlib import Path
import json
from bs4 import BeautifulSoup
from article_cta import insert_inline_cta, validate_cta_layout

ROOT = Path(__file__).resolve().parents[1]
INLINE = '<section class="article-cta article-cta-inline"><p class="eyebrow">실행 기준 이어 보기</p><h3>내 업무에 적용하기</h3><p>중간 안내</p></section>'
END = '<section class="article-cta article-cta-end" id="article-end"><p class="eyebrow">다음 단계</p><h3>팀 적용 범위 확인</h3><p>마지막 안내</p></section>'
LONG = '사람의 검수와 운영 기록을 확인합니다. ' * 30


def fragment(text):
    return BeautifulSoup(text, 'html.parser')


def expect_rejected(html):
    try:
        validate_cta_layout(fragment(html))
    except ValueError:
        return
    raise AssertionError('Invalid CTA layout was accepted.')


for heading in ('실무 예: 콘텐츠 캠페인', '한 콘텐츠 캠페인에 네 요소를 적용해보기', '편집 응용 예시', '실행 체크리스트'):
    rendered = fragment(f'<h2>{heading}</h2><p>사례 설명</p><h2>도입 로드맵</h2><p>{LONG}</p><h2>출처 및 참고 자료</h2><p>공식 문서</p>')
    assert insert_inline_cta(rendered, INLINE)
    assert len(rendered.select('.article-cta-inline')) == 1
    snapshot = str(rendered)
    assert not insert_inline_cta(rendered, INLINE) and str(rendered) == snapshot
    rendered.append(fragment(END).section)
    validate_cta_layout(rendered)
print('PASS heading variants, practical insertion and idempotent repeated calls')

for html in (
    '<h2>개념 설명</h2><p>설명</p>',
    '<h2>적용 예시</h2><p>마지막 사례</p>',
    f'<h2>적용 예시</h2><p>사례</p><h2>출처 및 참고 자료</h2><p>{LONG}</p>',
    f'<h2>출처 예시</h2><p>링크</p><h2>References</h2><p>{LONG}</p>',
    f'<h2>적용 예시</h2><p>사례</p><h2>요약</h2><p>짧은 문장</p><h2>출처</h2><p>{LONG}</p>',
):
    rendered = fragment(html)
    snapshot = str(rendered)
    assert not insert_inline_cta(rendered, INLINE) and str(rendered) == snapshot
    rendered.append(fragment(END).section)
    validate_cta_layout(rendered)
print('PASS missing/final/reference/short-tail cases do not append a fallback CTA')
expect_rejected(INLINE + END)
expect_rejected(INLINE + '<h2>로드맵</h2><p>'+LONG+'</p>' + INLINE + END)
expect_rejected(INLINE + '<h2>요약</h2><p>짧은 문장</p>' + END)
expect_rejected(INLINE + '<h2>로드맵</h2><p>'+LONG+'</p>' + END.replace('팀 적용 범위 확인', '내 업무에 적용하기'))
expect_rejected(INLINE + '<h2>로드맵</h2><p>'+LONG+'</p>' + END.replace('마지막 안내', '중간 안내'))
expect_rejected(END + '<p>이후 본문</p>')
print('PASS build guard rejects adjacent, duplicate, identical-copy and misplaced end CTA panels')

posts = json.loads((ROOT/'content/blog/posts.json').read_text())
for post in posts:
    soup = BeautifulSoup((ROOT/'dist/blog'/post['slug']/'index.html').read_text(), 'html.parser')
    body = soup.select_one('.article-body')
    validate_cta_layout(body)
    ids = [a['data-cta-id'] for a in body.select('.article-cta [data-cta-id]')]
    assert len(ids) == len(set(ids)), post['slug']
    if post['slug']=='agentic-ai-harness-loop-graph-jev-marketer-guide':
        inline = body.select_one('.article-cta-inline')
        assert inline is not None
        assert inline.find_next_sibling('h2').get_text(strip=True).startswith('8.')
        assert body.select_one('#article-end') is not inline.find_next_sibling()
    print('PASS',post['slug'],len(body.select('.article-cta-inline')),'inline / 1 end')
print(f'PASS all{len(posts)} article layouts; no real analytics or lead submissions')
