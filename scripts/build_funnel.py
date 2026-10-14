"""Static funnel and public editorial resources; never embeds Google credentials."""
from pathlib import Path
from html import escape
import json
import markdown
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = [
    {'slug': 'rgctor-worksheet', 'title': 'R-G-C-T-O-R 업무 지시서 워크시트', 'summary': '역할·목표·맥락·도구·출력·검수를 한 장으로 정리하고 사람의 승인 기준을 남깁니다.'},
    {'slug': 'content-search-checklist', 'title': '콘텐츠·SEO·GEO 검색 점검표', 'summary': '초기 HTML·검색 메타·출처·승인·성과 해석을 체크하고 다음 개선 한 가지를 기록합니다.'}
]


def build_funnel(dist, head, header, footer, origin, site):
    config = json.loads((ROOT / 'content/funnel.json').read_text())
    approved = config['policy_approved'] is True
    modified = config['modified']
    email = escape(config['contact_email'], quote=True)
    routes = []
    (dist / 'assets/downloads').mkdir(parents=True, exist_ok=True)

    def save(path, title, description, body, page_type, content_id, noindex=False):
        style = '<link rel="stylesheet" href="/assets/funnel.css"><script src="/assets/funnel.js" defer></script>'
        graph = {'@context':'https://schema.org','@type':'WebPage','name':title,'description':description,'url':origin+path,'inLanguage':'ko-KR'}
        html = head(title, description, path, graph=graph, noindex=noindex).replace('</head>', style + '</head>')
        content_group = 'consulting' if page_type == 'consulting' else 'resources'
        html += f'<body class="blog-page" data-page-type="{page_type}" data-content-group="{content_group}" data-content-id="{content_id}" data-ui-variant="ux-v1" data-policy-approved="{str(approved).lower()}"><a class="skip-link" href="#main">本文으로 이동</a>{header}<main class="wrap blog-main funnel-main" id="main">{body}</main>{footer}'
        html = html.replace('>本文으로 이동<', '>본문으로 이동<')
        folder = dist / path.strip('/')
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'index.html').write_text(html)
        routes.append({'path': path, 'title': title, 'lastmod': modified, 'noindex': noindex})

    privacy = f'''<header class="funnel-heading"><p class="eyebrow">Privacy / 문의 처리</p><h1>문의 정보는 응대에만 사용합니다.</h1></header><div class="privacy-content"><p>{'' if approved else '이 안내는 운영자 확인 전 초안입니다. 사이트 내 접수는 아직 열리지 않았습니다. '}</p><h2>누가, 어떤 목적으로 처리하나요?</h2><p>운영 주체: {escape(config['operator'])}. 교육·강연 또는 팀 업무 적용 문의를 확인하고 답변하기 위해 처리합니다. 뉴스레터·광고·별도 마케팅 발송 동의로 사용하지 않습니다.</p><h2>무엇을 받나요?</h2><p>필수: 회신 이메일, 문의 유형, 관심 업무. 선택: 소속, 메모. 접수 시각·접수 ID·유입 글·CTA·UI 버전·동의문 버전·처리 상태를 함께 기록합니다. 메모에는 고객 명단·비밀번호·민감정보를 적지 마세요.</p><h2>어디에, 얼마나 보관하나요?</h2><p>Google 스프레드시트에 비공개로 보관하고, 사이트 운영자의 문의 담당 계정에서 확인합니다. Google Apps Script와 Vercel이 문의 전달·저장 경로로 사용됩니다. {escape(config['retention'])}</p><p>오남용 방지를 위해 IP의 원문 대신 서버에서 날짜별로 생성한 해시 표식을 최대 2분간 임시 요청 제한에 사용합니다. 이 값과 원문 IP는 문의 시트에 기록하지 않습니다.</p><h2>동의를 거부하거나 삭제를 요청할 수 있나요?</h2><p>필수 수집·이용 동의를 거부할 수 있으며 이 경우 사이트 내 접수는 사용할 수 없습니다. 별도 이메일로 직접 문의할 수 있습니다. 열람·정정·삭제 요청은 <a href="mailto:{email}">{email}</a>로 보내주세요.</p><h2>분석 이벤트에는 무엇을 보내나요?</h2><p>폼 시작·오류 유형·저장 성공 등 행동과 페이지 문맥만 사용합니다. 이메일·소속·메모 원문은 GA4·Meta 맞춤 이벤트에 보내지 않습니다. 분석 차단 여부와 관계없이 문의 접수는 동작합니다.</p><p class="funnel-note">안내 버전: {escape(config['policy_version'])}. 이 페이지는 실제 운영 기준을 안내하며 법률 자문이나 적법성 보증이 아닙니다.</p><a class="text-link" href="/consulting">문의 화면으로 돌아가기 →</a></div>'''
    save('/privacy', '문의 개인정보 수집·이용 안내', '팀 적용 문의의 수집 항목·목적·비공개 Google Sheets 저장·보유·삭제 요청 방법을 안내합니다.', privacy, 'privacy', 'inquiry-privacy', noindex=True)

    def field_error(name):
        return f'<p class="field-error" id="error-{name}"></p>'

    contact = f'''<header class="funnel-heading"><p class="eyebrow">For teams / 교육 · 업무 운영</p><h1>팀에서 바꾸고 싶은<br>업무 한 가지부터 알려주세요.</h1><p class="section-copy">교육·강연의 주제, AI 업무 지시·검수·승인 구조의 적용 범위를 함께 살펴봅니다. 계약이나 구매 신청이 아닌 문의입니다.</p><p id="consulting-source" class="funnel-note" hidden><a href="/blog">읽던 글로 돌아가기 →</a> · 글에서 다룬 업무를 문의에 연결합니다.</p></header><div class="funnel-grid"><section class="funnel-panel" aria-labelledby="form-title"><h2 id="form-title">팀 적용 문의</h2><p class="funnel-note">필수 입력은 3개입니다. 소속과 자세한 메모는 나중에 적어도 됩니다.</p><div id="form-unavailable"><p>사이트 접수 연결을 확인하고 있습니다. 아래 이메일로 문의하시면 같은 운영자에게 전달할 수 있습니다.</p><a class="button primary" href="mailto:{email}?subject=AI%20Agent%20%ED%8C%80%20%EC%A0%81%EC%9A%A9%20%EB%AC%B8%EC%9D%98" data-position="consulting-fallback">이메일로 문의하기</a></div><form id="consulting-form" class="funnel-form" novalidate hidden><label for="email">회신 이메일 <span class="funnel-note">(필수)</span></label><input id="email" name="email" type="email" autocomplete="email" maxlength="254" required aria-describedby="email-help error-email"><p class="funnel-note" id="email-help">답변을 받을 주소를 적어주세요.</p>{field_error('email')}<label for="inquiry_type">문의 유형 <span class="funnel-note">(필수)</span></label><select id="inquiry_type" name="inquiry_type" required aria-describedby="error-inquiry_type"><option value="">선택해주세요</option><option value="education">교육·강연</option><option value="workflow">팀 업무·검수 체계 적용</option><option value="undecided">아직 정하지 못했어요</option></select>{field_error('inquiry_type')}<label for="work_area">관심 업무 <span class="funnel-note">(필수)</span></label><select id="work_area" name="work_area" required aria-describedby="error-work_area"><option value="">선택해주세요</option><option value="content">콘텐츠 제작·업무 지시</option><option value="review">검수·승인·운영 기준</option><option value="performance">광고·CRM·성과 해석</option><option value="undecided">업무 범위부터 함께 정하고 싶어요</option></select>{field_error('work_area')}<details><summary>소속·자세한 상황 덧붙이기 (선택)</summary><label for="organization">소속 (선택)</label><input id="organization" name="organization" autocomplete="organization" maxlength="100" aria-describedby="error-organization">{field_error('organization')}<label for="message">메모 (선택)</label><textarea id="message" name="message" maxlength="1500" rows="4" aria-describedby="message-help error-message"></textarea><p class="funnel-note" id="message-help">현재 막히는 업무 한 가지면 충분합니다. 고객 정보·비밀번호·민감정보는 쓰지 마세요. 최대 1,500자.</p>{field_error('message')}</details><div class="funnel-honey" aria-hidden="true"><label for="website">이 항목은 비워두세요.</label><input id="website" name="website" type="text" tabindex="-1" autocomplete="off"></div><p class="funnel-note">문의 응대를 위해 필수 3개 항목과 선택해 입력한 내용을 비공개 Google 스프레드시트에 보관합니다. {escape(config['retention'])} 마케팅 발송에 사용하지 않습니다.</p><label class="consent" for="consent"><input id="consent" name="consent" type="checkbox" required aria-describedby="error-consent"><span>[필수] <a href="/privacy" target="_blank" rel="noopener">문의 개인정보 수집·이용 안내 (새 창)</a>를 확인하고 동의합니다.</span></label>{field_error('consent')}<p id="form-status" class="funnel-status" role="status" aria-live="polite" tabindex="-1"></p><button class="button primary" type="submit" data-cta-id="consulting-submit">팀 적용 문의 남기기</button><p class="funnel-note">제출은 계약 체결이나 구매가 아닙니다. 회신은 입력하신 이메일로 진행하며 답변 시점을 미리 보장하지 않습니다.</p></form><section id="form-success" tabindex="-1" hidden><h2>문의가 저장되었습니다.</h2><p>비공개 문의 시트에 접수되었습니다. 입력한 이메일로 내용을 검토해 회신합니다. 같은 내용은 다시 제출하지 않으셔도 됩니다.</p><p class="funnel-note">별도 접수 확인 메일은 자동 발송하지 않습니다.</p><div class="funnel-actions"><a class="button secondary" href="/resources">기다리는 동안 워크시트 보기</a><a class="text-link" href="/blog">블로그로 돌아가기 →</a></div></section><noscript><p>사이트 내 접수에는 JavaScript가 필요합니다. 아래 이메일로 문의할 수 있습니다.</p></noscript><p class="funnel-note">직접 연락: <a href="mailto:{email}" data-position="consulting-direct">{email}</a></p></section><aside><h2>이런 장면을 함께 살펴봅니다.</h2><ul class="funnel-steps"><li>팀 공통의 AI 업무 지시·결과물 기준 세우기</li><li>콘텐츠 검수·승인·기록 흐름 정리</li><li>광고·CRM·리포트에서 사람의 판단 경계 정하기</li><li>도서 기반 교육·강연의 대상과 주제 확인</li></ul><h3>제출 후에는</h3><ol class="funnel-steps"><li>문의가 시트에 저장되면 화면에서 알려드립니다.</li><li>운영자가 내용과 적용 범위를 확인합니다.</li><li>입력한 이메일로 필요한 내용을 이어갑니다.</li></ol><p class="funnel-note">공개 글은 출처 기반 편집 콘텐츠입니다. 사례의 예시를 실제 고객 성과나 확정된 서비스 범위로 보장하지 않습니다.</p><hr><p>개인 학습이 먼저라면</p><a class="text-link" href="/#contents">책 전체 구성 확인 →</a><p>지금 바로 작성해보려면</p><a class="text-link" href="/resources">공개 워크시트 2종 보기 →</a></aside></div>'''
    save('/consulting', 'AI 마케팅 교육·팀 업무 적용 문의', 'AI Agent 업무 지시·검수·승인 구조와 도서 기반 교육·강연의 적용 범위를 문의하세요. 개인 학습과 팀 적용 경로를 구분합니다.', contact, 'consulting', 'team-consulting')

    cards = []
    for resource in RESOURCES:
        slug, title = resource['slug'], resource['title']
        source = (ROOT / 'content/resources' / (slug + '.md')).read_text()
        (dist / 'assets/downloads' / (slug + '.md')).write_text(source)
        rendered = BeautifulSoup(markdown.markdown(source, extensions=['fenced_code','tables','sane_lists']), 'html.parser')
        if rendered.h1: rendered.h1.decompose()
        body = f'''<header class="funnel-heading"><p class="eyebrow">Public worksheet / 이메일 등록 없음</p><h1>{escape(title)}</h1><p class="section-copy">{escape(resource['summary'])}</p><p class="funnel-note">Command Marketing 신규 편집 응용 자료 · AI 초안 활용 · 도서 원본 PDF가 아닙니다. 다운로드를 문의 접수로 집계하지 않습니다.</p><div class="funnel-actions"><a class="button primary" href="/assets/downloads/{slug}.md" download data-resource-id="{slug}" data-position="resource-top" data-cta-id="resource-download">작성용 Markdown 받기</a><button class="button secondary" type="button" data-copy-resource="resource-source">작성용 원문 복사</button></div><a class="text-link" href="/resources">워크시트 전체 보기 →</a></header><article class="resource-body">{rendered}</article><details class="resource-body"><summary>작성용 원문 펼치기</summary><pre class="resource-source" id="resource-source">{escape(source)}</pre></details><section class="article-end"><h2>팀의 실제 업무에 적용하려면.</h2><p>공개 자료로 먼저 작성해보고 팀 공통 기준이 필요한 부분을 문의하세요.</p><a class="button primary" href="/consulting?work={'content' if slug == 'rgctor-worksheet' else 'review'}&amp;intent=workflow&amp;cta=resource-team" data-consulting-path data-position="resource-end" data-cta-id="resource-team">팀 적용 범위 문의</a></section>'''
        save('/resources/' + slug, title, resource['summary'] + ' 공개 HTML 미리보기와 편집 가능한 Markdown을 이메일 등록 없이 제공합니다.', body, 'resource_detail', slug)
        cards.append(f'<article><p class="eyebrow">HTML 미리보기 + Markdown</p><h2>{escape(title)}</h2><p>{escape(resource["summary"])}</p><a class="button secondary" href="/resources/{slug}" data-resource-id="{slug}" data-position="resources-index" data-cta-id="preview-{slug}">작성 항목 미리 보기</a></article>')
    save('/resources', 'AI 마케팅 공개 워크시트·검색 점검표', 'R-G-C-T-O-R 업무 지시서와 콘텐츠·SEO·GEO 검색 점검표를 미리 보고 편집 가능한 Markdown으로 받으세요. 이메일 등록 없이 제공하는 신규 편집 응용 자료입니다.', '<header class="funnel-heading"><p class="eyebrow">Resources / 바로 작성하는 운영 기준</p><h1>읽은 내용을,<br>내 업무 한 장으로.</h1><p class="section-copy">이메일 등록 없이 열고 작성하는 공개 워크시트 2종입니다. 개인정보나 비공개 고객 자료는 쓰지 마세요.</p><p class="funnel-note">AI 초안을 활용한 Command Marketing 신규 편집 응용 자료이며 도서 원본 PDF가 아닙니다.</p></header><div class="resource-list">' + ''.join(cards) + '</div>', 'resource_index', 'public-resources')
    return routes
