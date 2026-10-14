# AI 검색 기술 SEO 체크리스트: 초기 HTML부터 크롤러·스키마까지

AI 검색에서 발견될 가능성을 높이는 첫걸음은 비밀스러운 AI 전용 태그가 아니라, 검색엔진이 페이지를 읽고 이해할 수 있는 기본 구조를 만드는 일입니다. 사용자가 찾는 답이 초기 HTML에 보이고, 중복 URL은 일관된 canonical로 정리되며, sitemap과 robots.txt가 올바르게 작동해야 합니다. Article·BreadcrumbList는 실제 페이지 정보를 설명하는 보조 신호일 뿐 노출 보증이 아니며, OAI-SearchBot과 GPTBot은 목적이 다릅니다. 이 글은 2026년 10월 14일 기준 공개 자료를 바탕으로 마케터와 팀 리더가 개발팀과 점검할 기준을 정리합니다.

## 1. 답의 핵심을 초기 HTML에서 바로 읽히게 하기

검색 시스템은 결국 공개되어 있고 접근 가능한 페이지의 정보를 발견하고 해석해야 합니다. 그래서 핵심 답변, 페이지 제목, 본문 제목과 주요 문장이 브라우저에서 실행되는 스크립트 뒤에만 숨어 있지 않은지 확인하세요. Google은 JavaScript 콘텐츠도 처리할 수 있지만, 기술적 복잡성을 늘리지 않으려면 사용자가 얻을 핵심 정보와 내부 링크를 서버가 반환하는 HTML에도 담는 편이 안전합니다. 시맨틱 태그를 완벽하게 맞추는 게 필수 조건은 아니지만, `<main>`, `<article>`, `<h1>`·`<h2>` 같은 구조는 사람과 보조기술이 문서를 탐색하는 데 도움이 됩니다.[1] [2]

예를 들어 “제품 상세 정보를 읽는 AI 에이전트가 무엇을 확인해야 하나?”라는 질문에 답하는 글이라면, 첫 화면에 “가격·재고·배송 조건을 한 페이지에서 확인할 수 있게 하고 변경 시점을 명시한다”처럼 직접적인 답을 둔 뒤, 각 항목의 기준과 예외를 풀어주세요. 이 문장은 응용 예시이며 특정 도서의 원문이나 저자 발언이 아닙니다. 핵심 답변과 근거, 적용 범위가 분명한 콘텐츠가 흔한 요약보다 독자에게 더 쓸모 있습니다. Google도 생성형 검색을 위한 특별한 HTML 또는 별도 schema가 아니라 크롤링 가능성, 유용하고 독창적인 콘텐츠, 명확한 구조 등 기존 SEO 원칙을 안내합니다.[1] [3]

GEO 연구는 생성형 엔진 응답에서 콘텐츠 가시성을 평가하는 벤치마크와 최적화 방법을 제안했고, 방법의 효과가 도메인에 따라 달라졌다고 보고합니다. 이는 연구의 실험 환경에 관한 결과이지 특정 사이트의 유입 증가 예측이나 노출 보장이 아닙니다.[11]

## 2. canonical·sitemap·robots.txt는 각자 역할대로

먼저 한 페이지에 추적 매개변수, 대소문자, 슬래시, HTTP/HTTPS, www 유무만 다른 URL이 생기는지 조사합니다. 대표 URL을 정했다면 페이지 `<head>`에 절대 주소의 자기참조 canonical을 두고 내부 링크와 sitemap도 같은 주소를 가리키게 하세요. 예를 들어 `https://example.com/guide/`가 대표 주소라면 캠페인 매개변수가 붙은 URL도 그 주소를 canonical로 표시합니다. Google은 리디렉션을 강한 canonical 신호, `rel="canonical"`을 강한 신호, sitemap 포함을 약한 신호로 설명합니다. 신호가 서로 충돌하지 않도록 통일하는 것이 핵심입니다.[4]

sitemap은 중요한 URL을 발견하도록 돕는 목록이지, 색인이나 검색 결과 노출 신청서가 아닙니다. 200 상태로 열리는 정규 URL, 실제로 색인되길 원하는 페이지 위주로 갱신하고 Search Console에서 제출·오류를 확인하세요. `robots.txt`는 크롤링 접근을 관리합니다. 차단만으로 검색 결과에서 URL이 사라지는 것은 아니므로, 공개 검색에서 제외하려는 페이지에는 `noindex`를 검토하되 검색 로봇이 그 지시를 읽을 수 있도록 크롤링 차단과 충돌하지 않게 해야 합니다. 즉 robots 차단은 비공개 처리나 색인 차단의 대체물이 아닙니다.[5] [6]

## 3. Article·BreadcrumbList는 보이는 내용과 일치시킨다

블로그 게시물에는 `Article` 또는 `BlogPosting` 구조화 데이터를 적용해 제목, 작성자, 대표 이미지, 게시·수정 시점 같은 정보를 기계가 이해하도록 표현할 수 있습니다. 실제 페이지에 보이는 제목·작성자와 마크업의 값이 같아야 하며, 존재하지 않는 작성자나 검증되지 않은 경력을 넣어서는 안 됩니다. 예컨대 페이지에 게시 조직만 표시된다면 저자를 특정 개인으로 임의 지정하지 말고, 실제 편집 정책에 맞는 주체를 사용합니다. Google은 Article 마크업이 페이지를 이해하고 제목·이미지·날짜를 표시하는 데 도움을 줄 수 있다고 설명하지만, 적용 자체가 리치 결과를 보장하지는 않습니다.[7]

`BreadcrumbList`는 “마케팅 > AI 활용 > 실무 가이드”처럼 독자가 실제로 이해하는 사이트 내 위치를 표현합니다. 각 단계의 순서와 이름을 HTML 화면의 이동 경로와 맞추고, 구조화 데이터 테스트와 URL 검사로 배포 후 결과를 확인하세요. 빵부스러기 표시는 검색 결과 형식의 하나일 수 있지만, 이를 추가했다고 모든 검색에서 항상 같은 형태로 보이는 것은 아닙니다.[8] 구조화 데이터는 숨겨진 키워드 저장소가 아니라 화면에 있는 사실을 명료하게 설명하는 표기입니다.

FAQ도 질문과 답을 독자가 읽을 수 있게 본문에 제공할 수 있습니다. 다만 FAQ 페이지의 유용성과 FAQ 스키마가 Google 리치 결과 자격은 서로 다른 문제입니다. Google은 2026년 5월 7일부터 FAQ 리치 결과를 더 이상 표시하지 않는다고 공지했습니다. 그러므로 FAQPage 마크업을 넣으면 SERP가 확장되거나 AI 검색에 인용된다고 약속하지 마세요. 질문이 반복해서 접수되는 고객지원 글에 명확한 답을 싣는 등 독자 효용이 있을 때 FAQ를 작성하면 됩니다.[9]

## 4. OAI-SearchBot과 GPTBot의 크롤링 목적을 구분한다

OpenAI의 공식 문서에서 `OAI-SearchBot`은 ChatGPT 검색 결과에 웹사이트를 노출하기 위한 검색 크롤러이고, `GPTBot`은 학습에 사용될 수 있는 콘텐츠를 수집하는 크롤러로 구분됩니다. 두 설정은 독립적입니다. 따라서 ChatGPT 검색에서의 발견을 허용하면서 모델 학습 목적의 크롤링은 허용하지 않으려는 사이트라면, robots.txt에서 각 User-agent 정책을 따로 검토해야 합니다. 어느 쪽을 허용하든 인용·노출을 보장하지 않으며, CDN·방화벽에서도 해당 요청이 실제로 통과하는지 로그와 함께 점검하세요.[10]

`llms.txt`는 일부 서비스가 읽도록 사이트 정보를 정리해 제공하는 비표준 보조 문서로 운영할 수 있지만, 공통 표준이나 검색 노출 스위치로 취급하면 안 됩니다. Google은 해당 파일이 Google Search의 생성형 기능에 필요하지 않고, 만들거나 유지해도 Google 검색 가시성·순위에 영향을 주지 않는다고 명시합니다.[1] 유지한다면 사이트 개요와 핵심 자료로 연결하는 편의 문서로 한정하고, 본문 HTML·내부 링크·크롤러 접근 같은 기본을 대신한다고 보지 마세요.

## 5. 배포 전 팀 체크리스트

마케터는 사용자의 질문을 한 문장으로 정리하고, 팀이 실제로 답할 수 있는 근거와 예외를 본문에 넣습니다. 개발자는 템플릿 기준으로 초기 HTML, 응답 코드, canonical, sitemap, robots 규칙과 크롤러 차단 여부를 확인합니다. SEO 담당자는 구조화 데이터가 화면과 일치하는지 테스트하고 Search Console의 색인·크롤링·검색 실적을 관찰합니다. 변경 뒤에도 색인과 노출에는 시간이 걸릴 수 있고 결과가 보장되지 않으므로, URL 검사 결과와 수집 로그를 함께 봅니다.[1] [7]

게시 전 빠르게 확인할 항목은 다음과 같습니다.

- [ ] 첫 화면에 질문에 대한 직접 답과 이를 뒷받침하는 본문 텍스트가 있는가?
- [ ] 핵심 내용을 로그인·클릭·브라우저 스크립트 실행 없이는 전혀 읽을 수 없는 구조로 만들지 않았는가?
- [ ] 페이지 제목, H1, 본문 주제가 서로 맞고 내부 링크로 접근 가능한가?
- [ ] 대표 URL의 canonical이 절대 주소로 선언되고 내부 링크·sitemap과 일치하는가?
- [ ] sitemap에는 공개된 정규 URL을 담고, robots.txt는 필요한 크롤러를 의도치 않게 막지 않는가?
- [ ] Article·BreadcrumbList 값이 화면에 표시된 사실과 일치하는가?
- [ ] robots.txt와 CDN/WAF 설정에서 OAI-SearchBot과 GPTBot을 서로 다른 정책으로 점검했는가?
- [ ] llms.txt나 스키마를 노출 보장책으로 광고하지 않고, FAQ는 리치 결과 자격과 분리해 설명하는가?

『AI Agent를 지휘하는 마케터』(박충효 저)의 프레임인 Role·Goal·Context·Tool·Output·Review를 이 글에서 실무 점검 렌즈로 응용하면 팀의 책임이 선명해집니다. 역할(Role)은 누가 페이지와 기술 변경을 맡는지 정하고, 목표(Goal)는 독자의 질문에 어떤 답을 제공할지 합의합니다. 맥락(Context)은 제품·정책·대상 독자와 최신 근거를 담고, 도구(Tool)는 CMS·크롤링 진단·Search Console을 선택합니다. 산출물(Output)은 초기 HTML과 구조화 데이터까지 포함한 공개 페이지이며, 검토(Review)는 사실·접근성·기술 오류를 확인하는 과정입니다. 이는 책의 원문 인용이나 저자의 직접 발언이 아니라 편집팀의 적용 사례입니다. 사람은 목표를 정하고, 결과를 검수·승인하며, 공개 정보에 대한 최종 책임을 집니다.

## 자주 묻는 질문

### AI 검색에 잘 노출되려면 llms.txt를 꼭 만들어야 하나요?

아닙니다. 일부 도구를 위한 보조 문서로 둘 수는 있지만, Google 검색의 생성형 기능에 필요한 파일은 아니며 작성한다고 가시성이 보장되지 않습니다. 먼저 공개 HTML, 내부 링크와 크롤링 가능성을 점검하세요.[1]

### OAI-SearchBot을 허용하면 GPTBot도 허용해야 하나요?

아닙니다. OpenAI는 검색용 OAI-SearchBot과 모델 학습에 쓰일 수 있는 콘텐츠를 수집하는 GPTBot의 robots.txt 설정이 독립적이라고 설명합니다. 조직의 공개·학습 데이터 정책에 따라 각각 결정하세요.[10]

### FAQ 스키마를 추가하면 Google 검색에서 FAQ가 펼쳐지나요?

그렇게 단정할 수 없습니다. Google FAQ 리치 결과는 2026년 5월 7일부터 더 이상 표시되지 않습니다. FAQ 콘텐츠는 독자에게 실제 답을 제공하는 목적으로 작성하고, 스키마를 리치 결과 자격이나 AI 인용 보장으로 오해하지 마세요.[9]

## References

[1]: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide "Optimizing your website for generative AI features on Google Search"
[2]: https://developers.google.com/search/docs/appearance/ai-features "AI features and your website"
[3]: https://developers.google.com/search/docs/fundamentals/creating-helpful-content "Creating helpful, reliable, people-first content"
[4]: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls "How to specify a canonical URL"
[5]: https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview "Learn about sitemaps"
[6]: https://developers.google.com/search/docs/crawling-indexing/robots/intro "Introduction to robots.txt"
[7]: https://developers.google.com/search/docs/appearance/structured-data/article "Article structured data"
[8]: https://developers.google.com/search/docs/appearance/structured-data/breadcrumb "Breadcrumb structured data"
[9]: https://developers.google.com/search/docs/appearance/structured-data/faqpage "FAQ structured data documentation and feature updates"
[10]: https://developers.openai.com/api/docs/bots "Overview of OpenAI Crawlers"
[11]: https://arxiv.org/abs/2311.09735 "GEO: Generative Engine Optimization"

---

편집: Command Marketing · AI 초안 활용, 공개 출처 기반 편집. 도서 발췌가 아닌 실무 응용 콘텐츠.
