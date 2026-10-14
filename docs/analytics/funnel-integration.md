# 전환 UX·Google Sheets 접수

기존 Vercel 정적 사이트의 /api/lead Node 함수가 입력·출처를 검증하고 서명한 요청만 Google Apps Script로 보냅니다. Apps Script는 소유자 권한으로 지정된 비공개 시트의 문의접수 탭에만 추가하며, 리드 조회/내보내기 엔드포인트를 제공하지 않습니다. 접수 ID 중복과 본문 해시를 확인하고 저장 성공 후에만 클라이언트에 성공을 반환합니다. 최초 설정은 로그인한 chunghyo@troe.kr 소유자만 가능하며 비밀 설정 파일은 저장소 밖에서 관리합니다. Sheet 관리 URL/Google 인증/서명 키를 공개 HTML·분석 payload·Git에 넣지 않습니다.

## 승인·운영 경계

문의 저장 대상으로 사용자가 Google 스프레드시트를 명시했습니다. 신규 외부 DB·메일 서비스는 사용하지 않습니다. Google 웹앱 최초 OAuth·공개 실행 경로·서버 환경값 연결과 개인정보 운영 기준이 확정되어야 실제 폼을 공개할 수 있습니다. 저장 확인 전에는 접수 완료를 표시하지 않으며, backend 미구성 시 실제 이메일 연락만 제공합니다. 알림 메일·뉴스레터·마케팅 동의는 자동 추가하지 않습니다. 시트 소유자는 접수 확인·응대·보유 정책에 따른 정리를 운영해야 합니다. 리드 수집은 분석 차단과 독립적으로 동작하고 원문 이메일/소속/메모는 GA4·Meta에 보내지 않습니다.

## 근거

- [Google Apps Script Web apps](https://developers.google.com/apps-script/guides/web): doPost·소유자 실행·최초 승인·웹앱 배포. Google OAuth 토큰을 클라이언트에 전달하지 않음.
- [Vercel Node.js runtime](https://vercel.com/docs/functions/runtimes/node-js): 루트 api/의 Node 함수, req.body·res.status/json 규약.

프런트 상단 배치와 CTA 변경은 ux-v1 배포 버전이며 A/B 실험 결과가 아닙니다. 기존 글의 검색 메타·원고·공유 이미지와 크롤러 정책을 유지하고 공개 자료만 새 경로에 포함합니다. 워크시트는 신규 편집 응용 자료로 도서 원본 PDF가 아닙니다.
