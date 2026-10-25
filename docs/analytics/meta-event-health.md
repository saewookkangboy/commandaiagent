# Meta 이벤트 활동·매칭 품질 운영 기준

2026-10-25 점검 대상은 Allrounder.im 데이터 세트2327515324662416과 book.allrounder.im이다. 개요 선택 기간은2026-09-27~2026-10-24다. 진단의 최근3일 활성 오류는 ‘현재 오류 없음’이었다. 과거 수신 목록과 최근 활동·매칭 품질은 서로 다른 정보다.

## 최근 활동 없음

`maturity_select`는 성숙도 단계의 실제 변경, `resource_access`는 자료 미리보기/다운로드 링크 조작, `start_situation_diagnosis`는 진단 시작이나 첫 조작, `select_solo_team_loop`는 상황 선택 후 시작점 실행이다. 단순 방문·페이지 로드만으로 발생시키지 않는다. 빈도가 낮다는 이유로 반복 전송하거나 실제 전환으로 바꾸지 않는다.

과거 `book_store_click`은 `click_book_purchase`로 통합되었다. 과거 ‘문의’/`Contact`는 현행 `inquiry_start`와 비교할 때 메일 작성 시작이라는 실제 동작과 적용일을 확인한다. 메일 열기는 문의 접수 완료가 아니다. 문의 폼의 저장 확인은 `lead_form_success`다. 기존 데이터와 계정 규칙을 삭제·복제하지 않고 과거/현행 이름을 분리해서 읽는다. 자동 설정 규칙의 실제 존재·적용 여부는 계정에서 별도 확인해야 한다.

## 6.1점과 업데이트 권장

직접 확인한 `section_view`, `scroll_depth`, `view_conversion_cta` 매칭 품질은6.1/10이었다. 세 이벤트 모두 IP주소·사용자에이전트·브라우저ID(fbp)의 공유 비율은100%였다. 매칭 품질은 서버 웹 이벤트에 동반한 고객 정보가 Meta 계정과 연결되는 품질이며, 최근48시간 데이터로 계산된다. 이벤트 동작 여부나 관여·실제 전환의 품질 점수가 아니다.[1]

점수 상승을 위해 문의 이메일·전화번호·이름·해시 사용자ID를 관여 이벤트에 새로 주입하지 않는다. 해시값도 제3자 고객정보 공유에 해당하므로 적법한 권리와 필요한 동의가 전제다. fbp가 이미 전달되므로 별도의 브라우저ID 저장소를 만들지 않는다. 실제 Meta 광고 유입에서 수집되는 클릭ID의 전달 문제는 해당 유입·기존 통합 경로의 증거가 있을 때만 확인하며, 임의 fbclid/fbc 값을 만들지 않는다.[1] [2]

## 코드 보강 범위

`PageView`에 발생 건별 난수 `event_id`와 네 번째 인자의 동일 `eventID`를 추가한다. 기존 맞춤24개 이벤트의 공통 ID와 의미는 유지한다. 사용자 식별자·새 쿠키·저장소·새 CAPI 서버는 추가하지 않는다. CAPI 중복 제거에는 서버가 같은 이벤트명과 ID를 보내야 한다. 브라우저 ID 구현만으로 서버 전송이나 중복 제거 완료를 주장하지 않는다.[3]

`section_view`는 제목의50% 이상 교차를 명시적으로 확인하고, 숨김 탭에 전달된 교차 상태를 기억한다. 탭이 다시 보이거나 BFCache로 복귀하면 현재 교차 중인 제목 중 아직 기록하지 않은 항목만 처리한다. 단순 `isIntersecting`의 낮은 교차비율이나 숨김 탭을 노출로 세지 않는다. 페이지당 섹션별1회 조건은 그대로다.

`maturity_select`는 초기 선택과 동일 단계 재선택, 양끝에서 Home/End를 누르는 무변경 조작을 제외한다. 다른 단계로 이동했다가 돌아오는 실제 변경은 기록한다. 활동 건수 증가를 위한 수정이 아니며 일부 과대집계가 줄 수 있다.

## 검증과 이후 확인

`node --check dist/assets/analytics.js`, `python3 scripts/check_analytics.py`, `python3 scripts/check_funnel.py`, `node scripts/check_lead_backend.cjs`로 문법·양 채널 동일 payload·ID·숨김/가시성·무변경 선택·기존 문의 모형을 확인한다. 브라우저 검사에서 운영 호스트를 로컬 파일로 모의하고 외부 요청은 모두 차단한다. 실제 문의·구매·분석 QA를 보내지 않는다.

웹 코드 변경은 기존 GitHub PR/main과 Vercel 운영 응답의 바이트 일치로 확인한다. Meta 점수 상승·추천 소멸·최근 활동 정상 표시에는 이후 실제 조건을 충족한 수신과 플랫폼 집계가 필요하다. 관측한 `section_view` 중복 제거 화면은 ‘데이터 구문 분석 중’이어서 정확한 완료율은 미확정이었다. 이를 오류 숨김이나 계정 설정 변경으로 처리하지 않는다.

## References

[1]: https://www.facebook.com/business/help/765081237991954 "Meta — About event match quality"
[2]: https://www.facebook.com/business/help/308855623839366 "Meta — Best practices for Conversions API"
[3]: https://www.facebook.com/business/help/823677331451951 "Meta — About deduplication for Meta Pixel and Conversions API events"
