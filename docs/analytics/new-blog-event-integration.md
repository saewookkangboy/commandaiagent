# 신규 블로그 GA4·Meta 픽셀 맞춤 이벤트 연동 가이드

**새 글은 이미 공통 이벤트 계약 v2.1에 연결되어 있으므로, 별도의 픽셀이나 클릭 태그를 추가하지 않습니다.** 먼저 기존 이벤트가 수신되는지 확인하고, GA4에서는 글·유입 문맥을 맞춤 측정기준으로 등록합니다. Meta에서는 저장 성공 이벤트에 글 유입 매개변수 규칙을 적용하면 됩니다. 이 문서는 현재 코드에 맞는 설정 가이드입니다. 계정의 실제 수신·맞춤 정의·맞춤 전환을 확인하거나 변경한 결과는 아닙니다.

기준일: 2026-10-15. 대상 글은 [마케터의 업무에 있어서 AI AGENT 구축은 왜 필요한가?](https://book.allrounder.im/blog/why-marketers-need-ai-agents)입니다. 함께 읽는 [워크플로우 정밀 설계·운영 글](https://book.allrounder.im/blog/marketer-ai-agent-workflow-design)에도 같은 계약이 적용됩니다. 두 글을 비교하려면 아래 조건의 슬러그만 바꾸세요.

## 1. 연결된 ID와 페이지 문맥

GA4 측정 ID는 `G-QK0BMHHNR5`, Meta Pixel ID는 `2327515324662416`입니다. GA4에서는 해당 측정 ID의 웹 데이터 스트림이 속한 **속성**을 선택하세요. 측정 ID와 속성의 숫자 ID는 다른 값입니다. Meta에서는 해당 픽셀에 연결된 데이터 소스를 선택합니다.

신규 글의 맞춤 이벤트에는 다음 공통 문맥이 들어갑니다. `event_id`는 발생 건마다 달라지며 아래에서 생략했습니다.

```json
{
  "event_version": "2.1",
  "page_path": "/blog/why-marketers-need-ai-agents",
  "page_type": "blog_article",
  "content_id": "why-marketers-need-ai-agents",
  "article_slug": "why-marketers-need-ai-agents",
  "content_group": "practical_guide",
  "ui_variant": "ux-v1"
}
```

`funnel_stage`는 행동마다 달라집니다. `view_blog_article`과 독서 관여는 `engagement`, 문의 CTA 클릭은 `intent`, `lead_form_success`는 `conversion`입니다. CTA 노출과 공개 자료 접근은 `exploration`입니다. 문의 페이지로 이동하면 `page_type=consulting`, `content_id=team-consulting`, `page_path=/consulting`으로 바뀝니다. 따라서 **문의 저장을 글의 `article_slug`로 필터링하면 안 됩니다.** 글에서 전달한 유입은 별도 `source_article_slug`로 확인합니다.

## 2. 새 글에서 확인할 이벤트

### 글 방문과 독서 관여

`view_blog_article`은 글 페이지가 표시될 때 페이지당 한 번 발생합니다. `article_slug=why-marketers-need-ai-agents`를 확인하세요. 링크를 클릭하지 않고 검색·외부 링크로 바로 방문해도 발생할 수 있습니다. 반면 `open_blog_article`은 내부 글 링크를 클릭한 시점의 이벤트입니다. 이 이벤트의 `article_slug`는 **이동할 글**, `page_path`와 `content_id`는 **클릭한 현재 페이지**입니다. 클릭과 도착을 두 번의 방문으로 합산하지 마세요.

`engaged_30s`는 탭이 보이는 누적 시간이 30초를 넘으면 한 번 발생합니다. `blog_article_complete`는 여기에 본문 아래 다음 행동 영역인 `#article-end`의 화면 도달이 함께 확인될 때 한 번 발생하며 `active_seconds=30`을 포함합니다. 정독이나 내용 이해를 확인하는 이벤트는 아닙니다. `scroll_depth`의 `percent=25|50|75|90`은 본문만이 아니라 전체 문서의 스크롤 도달 지점입니다. 목차·앵커 이동도 도달을 만들 수 있으므로 독서 완료로 바꾸어 해석하지 않습니다.

이번 글의 FAQ는 펼침 버튼이 없는 제목·본문 형식입니다. 따라서 FAQ 5개가 있다고 해서 `faq_expand` 5건이 발생하지 않습니다. 계측 누락이 아니라 UI에 맞는 현재 동작입니다.

### 문의 CTA 노출과 클릭

`view_conversion_cta`는 버튼 면적의 50% 이상이 보이고 탭이 보이는 상태로 1초 유지되면 페이지·CTA별 한 번 발생합니다. 버튼을 클릭하면 `click_consulting_path`가 발생합니다. 위치별 값은 다음과 같습니다.

- 본문 중간: `cta_id=inline-team`, `position=article-inline`.
- 글 하단: `cta_id=end-team`, `position=article-end`.
- 모바일 고정바: `cta_id=mobile-team`, `position=mobile-sticky`.

노출만으로 문의 클릭이나 리드 성공이 발생하지 않습니다. 모바일 고정바는 읽기 진행에 따라 나타나고 본문 CTA와 겹칠 때 숨을 수 있으므로 모든 모바일 방문에서 노출될 필요도 없습니다.

하단 문의 CTA의 실제 이동 주소는 다음과 같습니다. 중간·모바일 CTA에서는 `cta` 값만 해당 식별자로 바뀝니다.

```text
https://book.allrounder.im/consulting?from=why-marketers-need-ai-agents&work=review&intent=workflow&cta=end-team
```

`from`은 허용된 글 슬러그이며 문의 이벤트에 `source_article_slug`로 포함됩니다. `work`와 `intent`는 폼의 관심 업무·문의 유형을 미리 선택하는 데 사용합니다. 이 선택값과 URL 쿼리 전체를 맞춤 분석 payload로 복사하지 않습니다.

### 워크시트 접근

`resource_access`는 R-G-C-T-O-R 워크시트 링크 클릭 시 발생합니다. 글에서의 미리보기 값은 `resource_id=rgctor-worksheet`, `access_type=preview`이고 위치는 `article-inline` 또는 `article-end`입니다. CTA 식별자는 각각 `inline-resource`, `end-resource`이지만 **현재 `resource_access` payload에는 `cta_id`가 없습니다.** 위치 비교는 `position`으로 합니다.

자료 페이지의 실제 다운로드 링크 클릭은 `access_type=download`로 구분합니다. 이는 파일 수신 완료나 리드 생성이 아닙니다. 글의 워크시트 링크에는 `from`이 없으므로, 자료 페이지의 다운로드 이벤트까지 신규 글 유입 슬러그가 자동 보존되지 않습니다. 글 페이지의 `resource_access`로 진입 의도를 보고 자료 페이지에서의 다운로드는 별도로 해석하세요.

### 실제 문의 저장

`lead_form_start`는 폼 입력 항목의 첫 포커스, `lead_form_error`는 입력 검증·통신·서버·요청 제한 실패, `lead_form_success`는 서버가 비공개 Google Sheets 저장 또는 같은 접수의 기존 저장을 확인한 뒤 발생합니다. 모두 `form_id=team-consulting`을 포함합니다. 오류에는 `error_code=validation|network|server|rate_limited`만 추가됩니다.

글에서 직접 문의로 이동한 경우의 저장 성공 맞춤 payload 예시는 다음과 같습니다. **설명용 데이터이지 운영 콘솔에 보내는 테스트 코드가 아닙니다.**

```json
{
  "event_version": "2.1",
  "page_path": "/consulting",
  "page_type": "consulting",
  "content_id": "team-consulting",
  "content_group": "consulting",
  "ui_variant": "ux-v1",
  "source_article_slug": "why-marketers-need-ai-agents",
  "form_id": "team-consulting",
  "funnel_stage": "conversion"
}
```

이 이벤트에는 현재 글의 `article_slug`, `cta_id`, 이메일·소속·메모·IP·시트 접수 ID가 없습니다. CTA 식별자는 문의 URL과 시트 운영 기록에는 사용되지만 저장 성공의 분석 payload에는 포함되지 않습니다. 따라서 `lead_form_success AND cta_id=end-team`이라는 조건은 현재 코드와 맞지 않습니다. 이메일 링크 클릭인 `inquiry_start`와 문의 CTA 클릭도 저장 성공에 합산하지 마세요.

## 3. GA4 맞춤 측정기준과 핵심 이벤트 설정

먼저 실시간 또는 DebugView에서 이벤트·매개변수가 실제로 수신되는지 확인합니다. 이후 **관리 → 데이터 표시 → 맞춤 정의 → 맞춤 측정기준 만들기**에서 범위를 **이벤트**로 지정하고 실제 매개변수 이름을 그대로 입력합니다. 이미 등록된 키가 있다면 다시 만들지 않습니다. 맞춤 정의 생성에는 속성의 편집자 이상 권한이 필요하며, 데이터가 송신되고 정의가 생성된 뒤 보고서·탐색 반영에는 24~48시간이 걸릴 수 있습니다.[1]

우선 `article_slug`는 **현재 글**, `source_article_slug`는 **문의 유입 글**, `content_id`는 **현재 콘텐츠 식별자**, `cta_id`는 **노출·문의 클릭 버튼**, `position`은 **행동 위치**라는 이름으로 구분해 등록하세요. 아래 문의 퍼널의 `form_id` 조건을 사용하려면 이 키도 등록합니다. `error_code`를 추가하면 폼 오류를 분석할 수 있습니다. `resource_id`와 `access_type`은 공개 자료 분석이 필요할 때 등록합니다. `event_version`과 `ui_variant`는 버전 비교가 필요할 때 추가합니다. `content_group`은 기존 GA4 콘텐츠 그룹을 먼저 활용하고 같은 의미의 맞춤 정의를 중복 등록하지 않습니다.

`event_id`는 발생 건마다 다른 값이므로 맞춤 측정기준으로 등록하지 않는 편이 좋습니다. 이번 단계에서 24개 이벤트의 모든 키를 무조건 등록하지 말고 기존 등록과 남은 한도를 확인하세요. 이벤트명은 기본 측정기준을 사용합니다.

리드 목표는 기존 수신 이벤트 `lead_form_success`를 찾아 **관리 → 데이터 표시 → 이벤트**에서 핵심 이벤트로 지정하는 방식을 권장합니다. 기존 이벤트의 이름 옆 별표 등 표시 방식은 계정 UI에 따라 달라질 수 있습니다. 핵심 이벤트 지정은 이후 보고에 적용되며 과거 이벤트를 소급해 핵심 이벤트로 바꾸지 않습니다.[2] 방문·독서·워크시트 클릭을 모두 리드 목표로 지정하지 마세요. 이번 사이트는 실제 매출을 확인하지 않으므로 임의의 매출 금액도 넣지 않습니다.

별칭 이벤트 `agent_building_lead` 등을 추가 생성할 필요는 없습니다. 글별 저장은 기존 `lead_form_success`에 `source_article_slug` 필터를 적용하면 됩니다. 동일 행동을 `generate_lead` 등으로 다시 보내거나 GTM에서 별도 클릭 태그를 붙이면 보고가 중복될 수 있습니다.

## 4. GA4에서 신규 글의 문의 퍼널 보기

탐색의 퍼널 분석에서 우선 다음 흐름을 구성하세요. 각 단계는 **이벤트명과 해당 매개변수의 AND 조건**입니다.

1. 글 표시: `event_name=view_blog_article` 및 `article_slug=why-marketers-need-ai-agents`.
2. 문의 클릭: `event_name=click_consulting_path` 및 `content_id=why-marketers-need-ai-agents`.
3. 폼 시작: `event_name=lead_form_start`, `source_article_slug=why-marketers-need-ai-agents`, `form_id=team-consulting`.
4. 저장 확인: `event_name=lead_form_success`, `source_article_slug=why-marketers-need-ai-agents`, `form_id=team-consulting`.

일반적으로는 단계 사이 다른 행동을 허용하는 흐름으로 시작하세요. 보고 기간과 단계 간 시간 조건은 동일하게 유지합니다. 독서 관여는 별도 `view_blog_article → blog_article_complete` 흐름으로 봅니다. 모든 문의자가 먼저 30초 독서를 마쳐야 한다는 조건을 주 퍼널에 넣으면 빠르게 문의한 방문자를 제외할 수 있습니다.

CTA 위치 분석은 문의 클릭 이벤트를 `cta_id`·`position`으로 나누고, 같은 글·같은 버튼의 노출 이벤트와 비교합니다. 노출 대비 클릭률을 계산한다면 동일 기간의 사용자 기준 등 집계 단위를 맞추세요. 단순 이벤트 건수 비율은 재방문·반복 클릭 때문에 사용자 전환율과 같지 않습니다. 저장 성공을 버튼별로 나누는 필드는 현재 없으므로, CTA별 실제 저장 전환율을 직접 산출할 수 있다고 표시하지 않습니다.

글 유입 리드는 저장 이벤트에서 `source_article_slug`를 조건으로 보면 됩니다. **이 값은 현재 문의 URL에서 전달된 출처이지 최초 유입·최종 광고 클릭·멀티터치 기여 모델이 아닙니다.** 방문 후 다른 메뉴로 이동하거나 `from` 없는 문의 URL을 열면 값이 없을 수 있습니다. 값이 없는 성공 문의를 추정으로 이 글에 배정하지 마세요.

## 5. Meta 테스트와 맞춤 전환 규칙

[Meta Events Manager](https://www.facebook.com/events_manager2/)에서 지정된 픽셀 데이터 소스를 선택하고 **테스트 이벤트**의 웹 브라우저 이벤트 확인 기능을 사용합니다. 운영 글 URL을 열고 실제 읽기·CTA 클릭을 하면서 `view_blog_article`, `blog_article_complete`, `click_consulting_path`, `resource_access`의 매개변수를 확인합니다. 테스트 도구는 웹·앱 이벤트의 수신 확인을 위한 기능입니다.[3] 이벤트명이 대소문자까지 기존 계약과 일치하는지, 신규 글 슬러그가 전달되는지를 봅니다.

웹 테스트는 테스트 이벤트 화면을 열린 상태로 유지하고, 브라우저 이벤트 영역에 사이트 URL을 넣어 **웹사이트 열기**로 시작합니다. 일반 분석 화면에는 설정 후 30분 이상 지연되어 보일 수 있습니다. **활동 지우기**는 테스트 화면 표시를 정리하는 것이며 Events Manager·광고 보고·잠재고객 결과에서 테스트 활동을 삭제하는 방법은 아닙니다.[3]

수신 후 **맞춤 전환 → 맞춤 전환 만들기**에서 이름·데이터 소스·전환 이벤트를 정하고 **이벤트 매개변수** 규칙을 추가할 수 있습니다. 실제 선택한 이벤트가 보내는 키를 사용해야 합니다.[4] 다음 두 규칙을 구분해서 구성하세요.

**신규 글 유입 문의 저장**은 `lead_form_success`를 전환 이벤트로 선택하고, `source_article_slug`가 `why-marketers-need-ai-agents`와 같은 조건을 추가합니다. 별도 규칙으로 `form_id=team-consulting`도 추가합니다. 이름은 `AI Agent 구축 필요성 글 유입 문의 저장`처럼 실제 행위를 표시합니다. 리드 분석의 우선 후보이며 읽기나 클릭보다 하위 퍼널을 의미합니다.

**신규 글 문의 CTA 클릭**은 `click_consulting_path`와 `content_id=why-marketers-need-ai-agents`를 사용합니다. 특정 버튼만 보려면 별도 규칙으로 `cta_id=end-team` 등을 추가합니다. 이름에는 반드시 `문의 클릭`이라고 표시하고 저장 성공과 합산하지 않습니다. 관여를 추가로 구분한다면 `blog_article_complete` 및 `article_slug=why-marketers-need-ai-agents`를 사용할 수 있지만 이는 정독 보장이나 리드 완료가 아닙니다.

Meta에서는 별도로 추가한 규칙 사이에는 AND, 한 매개변수 규칙 안의 여러 후보값 사이에는 OR가 적용됩니다.[4] 예를 들어 구축 필요성 글과 설계·운영 글의 문의 저장을 함께 보려면 `source_article_slug` 규칙 한 개에 두 슬러그를 후보로 넣습니다. 같은 키가 두 슬러그와 동시에 같아야 하는 AND 규칙을 만들면 일치하지 않습니다.

키가 선택 목록에 없으면 먼저 선택한 이벤트의 수신 매개변수를 확인하세요. 문의 성공에 `cta_id`를 억지로 사용하거나, `/consulting` 방문 URL만으로 저장 성공을 대신 만들지 않습니다. 이미 송신되는 `source_article_slug`의 실제 수신·데이터 소스·매개변수 사용 가능 상태를 확인하고, 사용할 수 없다면 전체 저장 성공과 GA4 글별 분석을 분리해 운영합니다. 맞춤 전환을 생성했다고 즉시 광고 최적화에 적합해지는 것도 아닙니다. 수신량, 유효 문의, 데이터 소스 권한과 계정 제한을 확인한 뒤 판단하세요.[5] 이 문서 작성에서는 맞춤 전환이나 광고 목표를 실제 생성·변경하지 않았습니다.

## 6. 중복 없이 구현을 유지하는 방법

사이트가 이미 `/assets/analytics-config.js` 다음 `/assets/analytics.js`를 로드합니다. 공통 모듈은 한 발생 건을 GA4 `gtag('event', 이름, payload)`와 Meta `fbq('trackCustom', 이름, payload, {eventID})`에 전달합니다. GA4·Meta의 payload `event_id`와 Meta의 네 번째 인자 `eventID`는 같은 발생 건의 식별값입니다.

**이 호출을 HTML·GTM·버튼 onclick에 다시 추가하지 마세요.** 이벤트 관리자에서 같은 CTA 클릭을 다른 이름의 `Lead`로 설정하는 것도 현재 정의와 충돌할 수 있습니다. 새로운 글을 추가할 때는 `content/blog/posts.json`과 `content/analytics-events.json`의 허용 슬러그, 생성된 body 문맥과 CTA 속성을 유지하고 `python3 scripts/build_blog.py`로 다시 생성하는 방식입니다.

현재 사이트에는 Meta CAPI가 연결되어 있지 않습니다. Google Sheets 저장 서버가 있다는 이유만으로 픽셀·CAPI 중복 제거가 작동한다고 해석하지 마세요. `event_id`는 사용자 식별자나 시트 접수 ID도 아닙니다. 웹 SDK 차단·동의·브라우저 정책과 각 플랫폼의 기여 기간 차이 때문에 두 플랫폼의 집계가 완전히 같아야 한다는 기준도 적절하지 않습니다.

## 7. 실제 수신을 점검하는 순서

먼저 운영 글에서 GA4 실시간 수신을 확인합니다. DebugView를 사용하려면 개인 테스트 기기에 [Google Tag Assistant](https://tagassistant.google.com/)를 연결해 디버그 모드를 활성화한 뒤 해당 기기를 선택합니다. DebugView에는 디버그 모드가 필요하므로 일반 방문이 보이지 않는 것만으로 연동 실패라고 판단하지 않습니다. 개인정보·동의 설정에 따라 디버그 이벤트도 표시되지 않을 수 있습니다.[6]

글을 열면 `view_blog_article`의 슬러그를, 탭을 보이는 상태로 30초 이상 유지하고 하단에 도달하면 `blog_article_complete`를 확인합니다. 문의 CTA 노출은 `view_conversion_cta`, 클릭은 `click_consulting_path`의 위치·CTA ID로 구분합니다. 문의 페이지에서 입력 항목에 포커스를 주면 `lead_form_start`와 `source_article_slug`를 확인할 수 있습니다. 자료 페이지와 문의 페이지에서는 `article_slug`가 비어 있는 것이 정상입니다.

오류 검증은 개인정보를 넣지 않은 빈 제출로 `lead_form_error`와 허용된 `error_code`를 확인할 수 있습니다. 저장 성공의 실계정 수신 검증이 필요하면 운영자와 테스트 문의를 구분할 방법을 정한 뒤 수행하세요. 실제 회신 가능한 테스트 주소 등은 시트 저장 서버에만 제공하고 분석 payload에는 포함되지 않아야 합니다. 그 테스트는 실제 비공개 시트의 행을 만들 수 있습니다. 이번 가이드 추가에서는 실문의나 테스트 문의를 새로 제출하지 않았습니다.

운영 브라우저에서 글 방문·클릭 검증을 하면 분석 플랫폼에 테스트 트래픽이 들어갈 수 있습니다. 개발자·내부 트래픽 필터를 별도로 관리하고, 운영자의 확인 건을 유효 문의와 분리하세요. 코드 회귀 검사는 외부 요청을 차단한 모의 SDK로 수행하며 실제 플랫폼 수신 확인과는 다릅니다. 로컬·임시 미리보기·404에서는 사이트의 SDK 초기화와 맞춤 송신이 차단되므로 그 주소의 DebugView 누락도 정상입니다.

UTM은 캠페인 코드만 사용합니다. 예를 들어 다음 주소는 신규 글의 외부 캠페인 유입을 구분할 때 사용할 수 있습니다.

```text
https://book.allrounder.im/blog/why-marketers-need-ai-agents?utm_source=linkedin&utm_medium=organic_social&utm_campaign=agent_need_202610&utm_content=article_card
```

현재 맞춤 UTM 값은 검증을 통과한 **현재 페이지 URL**에 있을 때만 포함됩니다. 내부 문의·자료 이동까지 UTM을 저장해 이어 주는 기능은 없습니다. GA4 세션 유입 분석은 별개이며 글 출처 `source_article_slug`와 광고 기여를 같은 것으로 해석하지 않습니다. UTM이나 이벤트 매개변수에는 고객 이름·이메일·전화번호·URL 원문을 넣지 마세요. 맞춤 payload의 제외 규칙이 각 SDK의 자동 수집이나 전체 동의 정책까지 대신 통제하는 것은 아닙니다.

## References

[1]: https://support.google.com/analytics/answer/14239696?hl=en "Google Analytics — 이벤트 범위 맞춤 측정기준 만들기"
[2]: https://support.google.com/analytics/answer/13128484?hl=en "Google Analytics — 핵심 이벤트 지정과 반영 시점"
[3]: https://www.facebook.com/business/help/2040882565969969 "Meta — 웹 브라우저 및 앱 테스트 이벤트 도구"
[4]: https://www.facebook.com/business/help/462806641140703 "Meta — 이벤트 매개변수 규칙으로 맞춤 전환 필터링"
[5]: https://www.facebook.com/business/help/780705975381000 "Meta — 웹 맞춤 전환의 용도와 조건"
[6]: https://support.google.com/analytics/answer/7201382?hl=en "Google Analytics — DebugView와 개인 기기 디버그 모드"

작성: Manus AI · 운영 코드와 공식 안내를 기준으로 정리 · 2026-10-15
