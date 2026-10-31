# 구매 의도 측정과 Meta 광고 URL 설정

`click_book_purchase`는 교보문고·YES24·알라딘의 외부 도서 페이지로 이동하려는 **구매 의도 클릭**이다. 이 이벤트는 실제 주문·결제·매출을 확인하지 않는다. 따라서 Meta 맞춤 전환과 GA4 주요 이벤트의 표시 이름에도 ‘구매 완료’ 대신 ‘구매 의도’ 또는 ‘도서 구매 클릭’을 사용한다.

## 사이트에서 보내는 이벤트

랜딩의 구매 버튼은 하나의 클릭에 다음 호출을 각각 한 번만 보낸다.

```text
GA4:  gtag('event', 'click_book_purchase', payload)
Meta: fbq('trackCustom', 'click_book_purchase', payload, { eventID })
```

두 payload는 같은 일회성 `event_id`를 사용한다. `position`, `cta_id`, `link_domain`으로 버튼 위치와 선택한 서점을 구분한다. `lead_form_success`, `Lead`, `Purchase`, `InitiateCheckout`은 이 클릭에서 보내지 않는다.

## Meta 맞춤 전환 설정

Meta Events Manager에서 데이터 세트 `Allrounder.im`(Pixel ID `2327515324662416`)을 선택한 다음 **맞춤 전환 만들기**를 연다. 전환 이름은 `도서 구매 의도 · click_book_purchase`로 하고, 데이터 소스는 위 Pixel로 선택한다. 전환 이벤트 조건은 `click_book_purchase`와 일치로 지정한다. 세 서점을 합친 구매 의도 전환이 목적이므로 `link_domain` 또는 `cta_id`의 추가 필터는 넣지 않는다.

이 설정은 외부 서점으로 이동한 의도만 집계한다. 서점 결제 완료나 매출 최적화가 필요한 경우에는 서점 측에서 승인된 구매 완료 데이터가 제공되는 별도 연동이 필요하다. 이벤트 이름을 `Lead` 또는 `Purchase`로 대체하거나, 같은 버튼에 Events Manager 클릭 규칙을 추가하면 이중 집계될 수 있다.

## GA4 주요 이벤트 설정

GA4 측정 ID `G-QK0BMHHNR5`가 속한 속성에서 **관리 → 데이터 표시 → 이벤트**를 연다. `click_book_purchase`와 `view_conversion_cta`의 주요 이벤트 토글을 각각 켠다. 이미 지정되어 있으면 중복 이벤트를 만들지 않는다.

`click_book_purchase`는 클릭, `view_conversion_cta`는 CTA가 50% 이상 보이고 1초 동안 가시 상태를 유지한 노출이다. 따라서 두 주요 이벤트를 실제 주문이나 문의 저장 완료와 합산하지 않는다. 실제 문의 성과는 저장 확인 후 전송되는 `lead_form_success`를 별도로 본다.

## Meta 광고 URL 매개변수

Meta Ads Manager의 광고 수준 **추적 → URL 매개변수**에는 다음 값을 입력한다.

```text
utm_source=meta&utm_medium=paid_social&utm_campaign=261011_aiagentbook&utm_content={{ad.name}}
```

랜딩 페이지 URL은 다음처럼 루트 도메인만 사용한다.

```text
https://book.allrounder.im/
```

Meta가 `{{ad.name}}`을 실제 광고 이름으로 치환한다. 이 사이트의 맞춤 이벤트는 개인정보와 공백을 제외한 80자 이내의 캠페인 코드만 수집하므로, 광고 이름도 `cm_book_static_01`처럼 영문·숫자·밑줄·하이픈을 사용하는 것이 안전하다. 고객 이름, 이메일, 전화번호를 광고 이름이나 UTM에 넣지 않는다.

작성: Manus AI · 2026-11-01
