# GA4·Meta Pixel 공통 이벤트 정의서 v2.1

홈·블로그 목록·글 10편·문의·공개 자료 페이지에서 동일한 이벤트명과 맞춤 매개변수를 GA4 `gtag('event')`와 Meta `fbq('trackCustom')`에 보냅니다. 원본은 `content/analytics-events.json`이고 정적 설정은 `dist/assets/analytics-config.js`입니다. `analytics.js`가 SDK 초기화와 공통 전송을, `enhancements.js`가 진단·읽기 경로 UI의 실제 실행 시점을 담당합니다. GA4 ID `G-QK0BMHHNR5`와 Meta Pixel ID `2327515324662416`은 기존 값을 유지합니다.

맞춤 이벤트는 이름과 매개변수로 구성되며, GA4 보고서에서 사용자 정의 매개변수를 활용하려면 별도 맞춤 정의가 필요합니다.[1] GA4의 이름·매개변수 제한과 Meta 맞춤 이벤트 형식에 맞춰 소문자 snake_case와 짧은 식별값을 사용합니다.[2] [3]

## 공통으로 보내는 항목

모든 맞춤 이벤트는 `event_version=2.1`, `event_id`, `page_path`, `page_type`, `content_id`, `content_group`, `funnel_stage`를 공유합니다. 글 페이지에는 `article_slug`를, 도서 시리즈에는 숫자 `series_order`도 포함합니다. `page_type`은 기존 유형과 `consulting`, `resource_index`, `resource_detail`, `privacy`를 포함합니다. `content_group`은 기존 유형과 `consulting`, `resources`를 포함합니다. `funnel_stage`는 `exploration`, `engagement`, `intent`, 실제 저장 확인의 `conversion`입니다. `ui_variant`는 새 UX의 `ux-v1` 또는 기존 `legacy-v2`입니다. 허용된 10개 글 슬러그의 `from` 유입 문맥은 `source_article_slug`로만 포함하며 쿼리 전체를 전송하지 않습니다.

`event_id`는 이벤트 발생마다 새로 만든 일회성 식별자이며 사용자 ID가 아닙니다. 같은 발생 건의 GA4·Meta 맞춤 payload에 같은 값이 들어가고, Meta에는 네 번째 인자의 `eventID`로도 전달합니다. 이는 향후 CAPI와 연결할 때 사용할 수 있는 식별 규칙이지 현재 CAPI 연동이나 GA4 일반 맞춤 이벤트 자동 중복 제거를 뜻하지 않습니다.[4] 사이트 내부 중복은 단일 리스너·한 번 발화 조건으로 방지합니다.

현재 페이지 URL의 `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`은 형식 검증을 통과한 캠페인 표식만 최대80자로 포함합니다. 문자·숫자·점·밑줄·물결표·하이픈만 허용하며 이메일 표기, 공백, URL, 9~15자리 숫자열 등은 제외합니다. 고정된 캠페인명 목록을 운영하는 방식은 아니며 새 캠페인명도 같은 형식이면 허용합니다. 문자 형식 검사만으로 사람 이름 같은 개인정보를 완벽하게 판별할 수 없으므로 UTM에는 캠페인 코드만 넣고 개인정보를 사용하지 마세요. 쿼리 전체나 `fbclid`, `gclid`, 폼 입력값을 맞춤 payload에 복사하지 않습니다. 브라우저 저장소에 캠페인을 별도 저장하지 않으므로 다음 페이지의 맞춤 UTM 값은 해당 페이지 URL에 있을 때만 포함합니다. GA4 자체 세션·유입 처리는 별개입니다.

GA4 설정의 `page_location`은 정규 페이지 URL, `page_referrer`는 참조 사이트 origin만 사용합니다. 허용된 UTM을 GA4 공식 `campaign_source`, `campaign_medium`, `campaign_name`, `campaign_content`, `campaign_term` 설정으로 전달합니다.[5] 이 규칙은 사이트의 맞춤 송신 코드에 대한 것입니다. Meta SDK의 기본 URL·쿠키 수집, GA4 확장 측정, 관리자에서 생성한 이벤트와 동의 정책까지 대신 변경하거나 개인정보 미수집을 보장하는 것은 아닙니다.

## 공통 이벤트 24개

### 탐색

- `view_conversion_cta`: CTA 면적50% 이상이 보이는 상태로 가시시간1초 유지. `cta_id`, `position`; 페이지·CTA별 한 번. 노출일 뿐 클릭·리드 아님.
- `resource_access`: 공개 워크시트 링크 클릭. `resource_id`, `access_type`(`preview`/`download`), `position`. 파일 수신 완료나 문의 접수 아님.
- `preview_open`: 진단·팀 적용과 구분되는 도서 미리보기 CTA 클릭. 추가 항목 `position`.
- `start_situation_diagnosis`: 진단 CTA 또는 처음 진단 조작. `position`; 페이지당 한 번.
- `select_solo_team_loop`: SOLO·TEAM·LOOP 선택 후 내 상황 보기 실행. `situation`.
- `select_reading_path`: 추천 파트 경로 클릭. `situation`, `parts`(예: `3,5,7`).
- `select_personal_path`: 개인 학습용 책 구성 경로 클릭. `position`.
- `open_blog_article`: 글 링크 클릭. `article_slug`는 이동할 글, `position`은 클릭 위치. 글 도착이나 읽기 완료는 아님.
- `maturity_select`: 성숙도 단계 클릭·키보드 선택. `level`은 1~5. 초기 기본 선택은 전송하지 않음.

### 콘텐츠 관여

- `view_blog_article`: 글 페이지 로드. `article_slug`; 페이지당 한 번. 주의 집중이나 실제 독서를 의미하지 않음.
- `open_rgctor_example`: 응용 예시를 처음 펼침. `element`는 Role·Goal·Context·Tool·Output·Review; 요소별 페이지당 한 번.
- `open_day1_preview`: DAY1 훈련 처음 펼침; 페이지당 한 번. 체크박스 선택값은 수집·저장하지 않음.
- `part_expand`: 파트 처음 펼침. `part_number`는 1~7; 파트별 페이지당 한 번. 읽기 경로·해시 자동 펼침도 포함.
- `faq_expand`: FAQ 처음 펼침. `question_id`는 페이지의 항목 순번; 항목별 페이지당 한 번. 질문 문구를 전송하지 않음.
- `section_view`: 섹션 제목의50%가 화면에 처음 보임. `section_name`; 섹션별 페이지당 한 번.
- `scroll_depth`: 스크롤 발생 후 화면 하단이 문서25·50·75·90% 지점에 도달. `percent`; 기준별 페이지당 한 번. 프로그램에 의한 앵커 이동도 스크롤을 발생시킬 수 있음.
- `engaged_30s`: 탭이 보이는 누적 시간이30초를 넘김. `active_seconds=30`; 페이지당 한 번. 숨겨진 탭 시간은 제외하고 뒤로가기 캐시 복귀 시 재개.
- `blog_article_complete`: 본문 하단 도달과 누적 가시시간30초를 모두 충족. `article_slug`, `active_seconds=30`; 페이지당 한 번. 이전 버전의 하단 도달만 체크하던 지표와 기준이 달라졌으며 정독을 보장하지 않음.

### 구매·문의 의도

- `click_book_purchase`: 외부 구매 페이지 이동 클릭. `position`, `link_domain`, 선택 `cta_id`. 실제 구매 완료가 아님.
- `click_consulting_path`: 교육·강연·컨설팅 범위 안내 이동. `position`, 선택 `cta_id`. 문의 작성·접수가 아님.
- `inquiry_start`: 메일 작성 링크 클릭. `position`. 이메일 주소·제목·본문은 맞춤 payload에 넣지 않으며 발송·접수·리드 완료를 의미하지 않음.

### 사이트 내 문의 작성·저장

- `lead_form_start`: 공개된 접수 폼에 첫 포커스. `form_id=team-consulting`; 페이지당 한 번.
- `lead_form_error`: 입력 검증·통신·서버·요청 제한 실패. `form_id`, `error_code=validation|network|server|rate_limited`. 필드 내용·오류 원문은 보내지 않음.
- `lead_form_success`: 서버가 비공개 Google 시트 저장 또는 같은 접수의 기존 저장을 확인한 뒤 표시. `form_id`; 페이지당 한 번. 메일 링크·버튼 클릭·자료 접근만으로 발생하지 않음.

위 3개 이벤트에는 이메일·소속·메모·시트 접수ID·IP를 보내지 않습니다. 실제 저장 연결과 플랫폼의 이벤트 수신은 별도 검증 대상입니다.

## 기존 이름과 집계의 변경

구매 클릭은 `book_store_click`와 `click_book_purchase`를 함께 보내던 방식에서 `click_book_purchase` 하나로 통합합니다. 구매 버튼을 클릭할 때 보내던 Meta `ViewContent`는 제거합니다. 이 사이트에서 외부 서점의 실제 결제를 확인할 수 없으므로 `Purchase`·`purchase`·`InitiateCheckout`을 만들어 보내지 않습니다. Meta는 실제 구매 완료와 페이지 방문 등을 구분하는 표준 이벤트를 정의합니다.[3]

팀 안내 클릭을 `preview_open`으로도 기록하던 방식은 `click_consulting_path`로 분리합니다. 기존 `click_consulting_path`의 이메일 단계는 `inquiry_start` 하나로 분리하고 `Lead`·`generate_lead` 표준 이벤트는 중복 생성하지 않습니다. v2.1부터 사이트 폼의 실제 저장 확인만 `lead_form_success`로 분리합니다. 진단 Hero CTA는 `start_situation_diagnosis` 하나로 수집하고 별도 `preview_open`을 중복 전송하지 않습니다.

이전 데이터는 삭제하지 않습니다. 변경 후의 비교에는 `event_version=2.1`과 반영일을 사용하세요. 기존 v2.0의 19개 이벤트 의미는 유지하고 v2.1에서 노출·폼·자료 5개를 추가했습니다. 성숙도 `level`은 기존0~4 인덱스에서 사람이 읽는1~5 단계로 정규화했습니다. 같은 행동의 별칭을 다시 생성하는 GA4 관리자 규칙, GTM 태그, Meta 이벤트 설정 도구의 클릭 규칙이 있다면 별도로 대조해야 합니다.

## 계정에서 설정할 항목

웹 송신 구현과 계정 설정은 별개입니다. 이번 변경은 GA4 맞춤 정의·핵심 이벤트, Meta 맞춤 전환·광고 최적화 목표를 자동 등록하거나 바꾸지 않습니다. 실제 수신 확인은 GA4 DebugView/실시간과 Meta Events Manager의 Test Events에서 권한 있는 계정으로 수행해야 합니다. 코드·모의 SDK 검증만으로 플랫폼 수신 완료를 주장하지 않습니다.

GA4 탐색 보고서에서 필요할 때 이벤트 범위 맞춤 측정기준으로 `event_version`, `page_type`, `content_id`, `funnel_stage`, `position`, `article_slug`, `series_order`, `situation`, `element`, `part_number`, `question_id`, `percent`, `level`을 등록할 수 있습니다. `content_group`은 GA4의 기본 콘텐츠 그룹 필드입니다.[5] `ui_variant`, `cta_id`, `source_article_slug`, `form_id`, `error_code`, `resource_id`, `access_type`는 퍼널 분석이 필요할 때 선택적으로 이벤트 범위 맞춤 측정기준에 추가합니다. 계정의 측정기준 한도와 기존 등록을 먼저 확인하세요. `active_seconds`는 필요할 때 맞춤 측정항목으로 사용합니다. `event_id`는 고유값이 매우 많아 보고서 측정기준으로 등록하지 않는 것을 권장합니다.[1]

책 구매 클릭과 문의 시작을 핵심 이벤트 또는 맞춤 전환으로 사용할 경우 이름에 **구매 의도 클릭**, **문의 작성 시작**이라고 표시하고 실제 매출·리드 완료와 합산하지 마세요. Meta 맞춤 이벤트 송신과 맞춤 전환 생성은 다른 작업입니다.[3] 각 플랫폼의 차단·동의·기여 기간 차이 때문에 두 채널 집계 수가 완전히 같다고 보장할 수 없습니다.

실제 리드 목표는 저장 검증 후 `lead_form_success`를 GA4 핵심 이벤트/Meta 맞춤 전환으로 설정하는 것을 검토할 수 있습니다. 클릭 지표와 합산하지 말고, 완료 수뿐 아니라 운영자가 확인한 유효 문의 비율을 함께 보세요. 플랫폼 설정은 자동 변경하지 않았습니다.

## 재생성과 검증

`python3 scripts/build_blog.py`로 공통 설정과 페이지를 생성한 뒤 `node --check dist/assets/analytics.js`, `node --check dist/assets/analytics-config.js`, `python3 scripts/check_blog.py`, `python3 scripts/check_analytics.py`, `python3 scripts/check_funnel.py`, `node scripts/check_lead_backend.cjs`를 실행합니다. 전용 브라우저 검사는 운영 hostname을 로컬 파일로 모의 응답하고 모든 외부 요청을 차단해 GA4·Meta에 테스트 트래픽을 보내지 않습니다. 로컬·미리보기·404에서는 SDK 초기화와 맞춤 송신을 차단합니다. 기존 동의 관리 방식은 새로 도입하지 않으며 `commandTrackingEnabled=false`일 때 사이트의 맞춤 송신도 중단합니다.

## 신규 블로그에 적용하는 연동 가이드

2026-10-15 추가: 「마케터의 업무에 있어서 AI AGENT 구축은 왜 필요한가?」의 슬러그는 `why-marketers-need-ai-agents`이며 공통 이벤트 계약2.1·기존24개 이벤트가 이미 연결되어 있습니다. [신규 글 GA4·Meta 픽셀 연동 가이드](new-blog-event-integration.md)에 실제 CTA 식별값, payload 예시, GA4 맞춤 정의·핵심 이벤트·문의 퍼널, Meta 매개변수 기반 맞춤 전환과 실수신 확인 순서를 추가했습니다.

글 방문·문의 클릭은 현재 글의 `article_slug` 또는 `content_id`, 문의 저장은 `lead_form_success`와 `source_article_slug`로 구분합니다. `lead_form_success`에는 `cta_id`가 없으므로 CTA별 저장 전환율을 직접 산출할 수 있다고 표시하지 않습니다. 워크시트 이동에는 `from`이 없어 자료 다운로드까지 글 유입이 자동 보존되지 않습니다. 이번 글의 FAQ는 펼침 UI가 아니므로 `faq_expand`가 발생하지 않습니다.

가이드 추가는 새 픽셀·GTM 태그 설치, 이벤트 별칭 생성, GA4·Meta 계정 설정 변경을 뜻하지 않습니다. 실제 수신과 맞춤 정의·핵심 이벤트·맞춤 전환의 등록 상태는 권한 있는 계정에서 별도로 확인합니다.

## References

[1]: https://support.google.com/analytics/answer/12229021?hl=en "Google Analytics — Custom events and custom dimensions"
[2]: https://support.google.com/analytics/answer/9267744?hl=en "Google Analytics — Event collection limits"
[3]: https://developers.facebook.com/documentation/meta-pixel/implementation/conversion-tracking "Meta — Standard events, trackCustom and custom conversions"
[4]: https://developers.facebook.com/documentation/ads-commerce/conversions-api/deduplicate-pixel-and-server-events "Meta — Event ID and event name deduplication for Pixel and CAPI"
[5]: https://developers.google.com/analytics/devguides/collection/ga4/reference/config "Google Analytics — Campaign and page configuration reference"
