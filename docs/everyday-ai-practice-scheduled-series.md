# 일반 독자 AI Agent 실습 시리즈 예약 발행

이 시리즈는 사용자가 지정한 2026-10-29, 10-30, 11-02, 11-03, 11-04에 1편부터 하루 한 편씩 공개한다. 기존 사이트 예약 운영의 게시 시각인 **09:00 Asia/Seoul**을 적용한다. 10월 29일 슬롯은 이미 지났으므로 첫 공개는 당일 변경이 운영 배포된 뒤 진행하며, 10월 30일부터는 일회성 타이머가 지정일에 실행된다. 타이머 실행 시각은 즉시 사이트 공개 완료를 보장하지 않는다.

| 게시일·시각 (KST) | 편 | 슬러그 | 실습 산출물 |
| --- | --- | --- | --- |
| 2026-10-29 09:00 | 1. 반복 업무 발견 | `everyday-ai-practice-01-discovery` | 업무 관찰 카드 |
| 2026-10-30 09:00 | 2. 목적과 경계 | `everyday-ai-practice-02-purpose` | 목표·경계 카드 |
| 2026-11-02 09:00 | 3. 프롬프트 v1 | `everyday-ai-practice-03-prompt` | R-G-C-T-O-R 프롬프트 v1 |
| 2026-11-03 09:00 | 4. 테스트와 수정 | `everyday-ai-practice-04-test` | 테스트 기록과 v2 |
| 2026-11-04 09:00 | 5. 재사용과 운영 | `everyday-ai-practice-05-operation` | 개인 업무 운영 카드 |

## 예약 원본과 공개 경계

`content/scheduled/everyday-ai-practice/`에는 승인된 원고, metadata, 주제 섹션 정의, 1200×675 JPG/WebP 이미지, SHA-256 무결성 manifest를 둔다. 예약 자료는 기존 GitHub 저장소의 파일이므로 저장소를 직접 열람할 수 있는 사람에게는 소스 원고가 보일 수 있다. 그러나 미발행 글·이미지는 사이트의 `content/blog/posts.json`, `dist`, sitemap, `llms.txt`, `manus-routes.json`, 계측 allowlist에 넣지 않는다. 공개 페이지·검색문서에는 당일 승인된 한 편만 승격한다.

공개 섹션 `everyday-ai-practice`에는 그 시점까지 공개된 slug만 등록한다. 상세 글의 시리즈 내비게이션은 예약 manifest를 읽어 이미 공개된 글에는 링크를, 미발행 편에는 지정 날짜의 ‘발행 예정’ 표시를 사용한다. 새 편을 공개하면 이전 글의 시리즈 내비게이션도 재생성한다. 과거 공개 글의 `date`는 보존하고 실제 갱신 시 `modified`만 올린다.

## 당일 승격·검증

다음 명령은 현재 Asia/Seoul의 날짜와 시간을 확인해 오늘 슬롯이 맞을 때만 한 편을 로컬 작업 트리에 승격한다. `--dry-run`은 읽기 전용이며, 이전 편이 빠져 있거나 승인된 hash와 다르면 중단한다.

```sh
python3 scripts/publish_scheduled.py --schedule-dir content/scheduled/everyday-ai-practice --dry-run
python3 scripts/publish_scheduled.py --schedule-dir content/scheduled/everyday-ai-practice
python3 scripts/build_blog.py
python3 scripts/check_blog.py
python3 scripts/check_cta.py
python3 scripts/check_blog_sections.py
python3 scripts/check_series_analytics.py
python3 scripts/check_analytics.py
python3 scripts/check_funnel.py
node scripts/check_lead_backend.cjs
```

`python3 scripts/check_everyday_ai_practice_scheduled.py --full`은 별도의 임시 복사본에서 다섯 날짜를 순서대로 시뮬레이션한다. 게시 전 시각의 대기, 이전 편 누락 차단, 중복 재실행, 미발행 페이지·이미지·검색 문서 배제, 공개 섹션·FAQ·canonical·CTA·검색 메타·계측을 검사하며 실제 작업 트리의 `dist`는 변경하지 않는다.

실제 공개는 기존 `main` 최신본에서 날짜 전용 브랜치를 만들고 기존 PR·검사·Vercel 배포 경로를 사용한다. 새 GitHub Actions, 새 호스팅·계정, 강제 push는 만들지 않는다. PR 병합 후에는 `python3 scripts/verify_scheduled_production.py --schedule-dir content/scheduled/everyday-ai-practice --wait-seconds 600 --output <비공개 증거 파일>`을 실행해 운영 HTTP 응답의 상세 본문·canonical·OG/Twitter·FAQ·CTA·sitemap·`llms.txt`와 공개 예정 전후 페이지 상태를 확인한다. 운영 응답이 검증되기 전에는 공개 완료로 보고하지 않는다.

도서는 마케팅 실무서다. 주간 학습 메모, 실습 카드, 프롬프트, 예상 테스트 표본은 일반 독자용 편집 응용이며, 실제 사용자 사례·실행 결과·시간 절감·자동화 성과가 아니다. 자료 권한과 개인정보 보호, 원문 대조, 사람의 최종 판단을 유지한다.

## 예약 실행 상태

2026-10-29 기준 1편은 당일 배포 후 공개한다. 나머지 네 편은 각각 2026-10-30, 11-02, 11-03, 11-04 09:00 KST의 일회성 타이머로 실행한다. 타이머 설정이 승인·등록되기 전에는 자동 실행이 예약된 것으로 간주하지 않는다.
