# 구현 진행

- [x] 60초 진단: Hero 아래 SOLO/TEAM/LOOP 선택, 페이지 내 앵커 이동, 서버·팝업·개인정보 수집 없음.
- [x] 전후 비교: 업무 지시·검수·기록 카드 3개, 경계 설명 직전 배치.
- [x] R-G-C-T-O-R 신간 인스타그램 캠페인: 6개 펼침 카드와 목차 CTA, 응용 예시 표시.
- [x] 90초 경로: 개인 3·5·7 / 팀 2·3·7 / 광고·CRM·리포트 4·5·6 파트 앵커와 자동 펼침.
- [x] 3주 훈련 DAY 1: 세 질문 체크박스, 저장·분석 전송 없음, 훈련 전체 구조 CTA.
- [x] 7개 파트 결과물 미리보기, Part 6 광고와 랜딩 메시지 일치·실험 기록.
- [x] 개인·팀 CTA 분리, 팀 적용 장면 4개, 구매·조직 FAQ 분리.
- [x] 독립 블로그 5편: SEO·GEO·AIEO 용어 / 인용 콘텐츠 / 기술 SEO / R-G-C-T-O-R 운영 / 성과 측정. 공개 출처·FAQ·편집 고지, 목록·글·관련 글 연결.
- [x] 초기 HTML 본문, 글별 메타데이터·BlogPosting·BreadcrumbList, sitemap·llms 갱신, 기존 robots 보존, 404.
- [x] start_situation_diagnosis / select_solo_team_loop / open_rgctor_example / open_day1_preview / click_book_purchase / click_consulting_path 이벤트. 기존 추적 ID 보존, 미리보기 전송 차단.
- [x] 로컬·공개 미리보기 응답 및 상호작용·반응형 검증.
- [x] GitHub 인증·관리자 권한 확인. 최신 main에 검증된 패치를 충돌 없이 적용.
- [ ] `feat/landing-engagement-seo-blog` 브랜치 커밋·푸시 및 검토용 PR.
- [ ] 운영 도메인 배포: 최종 콘텐츠 확인·승인 이후 진행, 현재 보류.

검증 근거: 7개 공개 페이지의 원시 HTTP 본문·메타데이터·JSON-LD·sitemap 및 로컬/공개 200 응답, 실제 404 응답 확인. 자동 회귀검사에서 진단 3개, 경로별 파트 자동 열기, RGCTOR·DAY1 이벤트, DAY1 체크 무저장·무전송, 미리보기 추적 스크립트 차단, 390/768/1061/1440px 가로 넘침 없음, JS 없는 본문 탐색, 런타임 오류 0 확인. 단회 읽기 전용 검토의 보조 텍스트 대비 문제는 4.54:1 이상으로 수정. 새 Lighthouse 점수나 검색 노출 성과는 측정하지 않음.
