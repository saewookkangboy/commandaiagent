<p align="center">
  <img src="./dist/assets/book-3d.png" width="460" alt="AI Agent를 지휘하는 마케터 입체 표지">
</p>

<h1 align="center">AI Agent를 지휘하는 마케터</h1>

<p align="center">
  AI에게 일을 맡기고, 결과를 검수하고, 업무를 시스템으로 설계하는<br>
  <strong>커맨드 마케터를 위한 도서 프로모션 웹사이트</strong>
</p>

<p align="center">
  <code>Static HTML</code> · <code>Responsive</code> · <code>TROE × AX WORKS</code> · <code>박충효</code>
</p>

<p align="center">
  <a href="https://book.allrounder.im/"><strong>웹사이트 보기</strong></a>
</p>

---

## 프로젝트 소개

이 저장소는 박충효 저 『AI Agent를 지휘하는 마케터』의 핵심 메시지를 웹에서 경험할 수 있도록 만든 반응형 프로모션 사이트입니다.

단순히 AI 도구를 소개하는 대신, 마케터가 목표와 기준을 세우고 AI Agent에게 업무를 맡긴 뒤 최종 결과를 검수하는 **Command Marketing 운영 방식**을 시각적으로 전달합니다. 책 표지의 청록색 인상과 TROE의 절제된 브랜드 시스템을 비대칭 출판물 레이아웃으로 연결했습니다.

## 실제 화면

<p align="center">
  <img src="./docs/readme/site-preview.png" width="900" alt="AI Agent를 지휘하는 마케터 프로모션 사이트 데스크톱 전체 화면">
</p>

## 사이트에 담긴 내용

- **AI 활용 성숙도 5단계**: 도구 사용자에서 커맨드 마케터로 이동하는 과정을 인터랙티브 탭으로 탐색합니다.
- **R-G-C-T-O-R**: Role, Goal, Context, Tool, Output, Review로 구성한 AI 업무 지시서 구조를 설명합니다.
- **7개 파트 목차**: AI Agent 리터러시부터 리서치·콘텐츠·광고·CRM·운영 매뉴얼까지 책의 전체 흐름을 아코디언으로 제공합니다.
- **21일 훈련 플랜**: 업무 분해, 지시·검수 기준, 반복 운영의 세 단계 실천 방향을 제안합니다.
- **직접 답변 FAQ**: 책의 성격, 커맨드 마케터, R-G-C-T-O-R, 독자, 구성과 역할 분담을 질문–답변 구조로 제공합니다.
- **저자와 TROE**: 박충효의 마케팅·AI/AX 전문성과 강연·교육 문의 동선을 연결합니다.

## 빠르게 실행하기

별도 빌드나 패키지 설치가 필요하지 않습니다.

```bash
git clone https://github.com/saewookkangboy/commandaiagent.git
cd commandaiagent
python3 -m http.server 4173 --directory dist
```

브라우저에서 [http://localhost:4173](http://localhost:4173)을 열면 됩니다.

파일을 직접 확인하려면 `dist/index.html`을 브라우저에서 열어도 됩니다.

## 프로젝트 구조

```text
commandaiagent/
├── README.md
├── .github/
│   └── workflows/
│       └── deploy-pages.yml
├── .openai/
│   └── hosting.json
├── vercel.json
├── docs/
│   └── readme/
│       └── site-preview.png
└── dist/
    ├── index.html
    ├── robots.txt
    ├── sitemap.xml
    ├── llms.txt
    └── assets/
        ├── book-3d.png
        ├── book-3d.webp
        ├── book-cover.jpg
        └── book-flat.jpg
```

## 디자인 시스템

리디자인은 [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)의 Redesign - Preserve 원칙을 적용했습니다. 정보 구조와 SEO 자산은 유지하고 타이포그래피, 여백, 컬러 토큰, 모션, 핵심 섹션 구성을 순서대로 개선했습니다.

- Design Variance: `7`
- Motion Intensity: `5`
- Visual Density: `4`

| 역할 | 색상 | 용도 |
|---|---|---|
| Ink | `#101817` | 본문과 정보 위계 |
| Paper | `#EEF3F1` | 전체 페이지 배경 |
| Surface | `#F8FAF9` | 콘텐츠 표면 |
| Book Teal | `#007E71` | 단일 강조색과 인터랙션 |
| Dark Surface | `#0D1514` | 시스템 다크 모드 배경 |

타이포그래피는 별도 웹폰트 의존 없이 시스템 글꼴을 사용합니다. 카드 반경은 18px, 버튼은 pill 형태로 역할을 구분하며 모든 비대칭 레이아웃은 모바일에서 명시적으로 1열로 전환됩니다.

## 기술 구성

- HTML, CSS, Vanilla JavaScript 단일 페이지
- 외부 프레임워크와 런타임 의존성 없음
- 반응형 레이아웃과 `prefers-reduced-motion` 대응
- 시스템 설정에 따라 전환되는 라이트·다크 컬러 토큰
- 키보드 화살표로 이동할 수 있는 AI 성숙도 탭과 모바일 메뉴
- 키보드 접근이 가능한 링크·버튼·아코디언
- WebSite, WebPage, Organization, Person, Book, FAQPage를 연결한 JSON-LD `@graph`
- 이메일 기반 출간·단체 구매·강연 문의 CTA

## 배포

- 운영 도메인: [https://book.allrounder.im](https://book.allrounder.im)
- 호스팅: Vercel `chunghyos-projects`
- 보조 배포: GitHub Pages
- Vercel 출력 디렉터리: `dist`

## SEO · GEO 적용

- 검색 제목·설명·작성자·발행자·canonical·robots 메타 태그
- Open Graph와 X 카드 메타데이터 및 실제 도서 이미지 연결
- Google·Bing 검색 노출을 위한 무제한 스니펫과 큰 이미지 미리보기 허용
- `robots.txt`에서 Google·Bing 및 AI 검색 크롤링 허용
- ChatGPT의 `OAI-SearchBot`, Claude의 `Claude-SearchBot`·`Claude-User` 명시 허용
- 검색 크롤러와 모델 학습 크롤러를 분리해 `GPTBot`·`ClaudeBot` 학습 접근 차단
- canonical URL과 실제 수정일을 포함한 `sitemap.xml`
- AI 시스템이 핵심 사실과 신뢰 링크를 빠르게 확인할 수 있는 보조 문서 `llms.txt`
- 본문에 검색 의도와 바로 연결되는 직접 답변 FAQ와 정보 기준일 표시

`llms.txt`는 일부 AI 시스템을 위한 보조 문서이며 Google 검색 순위를 높이는 특수 규격으로 취급하지 않습니다. 검색·AI 노출의 기본은 공개 URL, 크롤링 가능성, 사람에게 유용한 본문, 일관된 구조화 데이터입니다.

## 검수 결과

| 항목 | 결과 |
|---|---|
| 데스크톱 렌더 | 1440 × 1000 전체 화면 확인 |
| 모바일 렌더 | 390 × 844 전체 화면 확인 |
| 가로 오버플로우 | 없음 |
| 브라우저 콘솔 오류 | 0건 |
| 로컬 이미지 누락 | 0건 / 원본 3종과 히어로 WebP 정상 로드 |
| 인터랙션 | 성숙도 탭, PART 07 아코디언 작동 확인 |
| 구조화 데이터 | JSON-LD 파싱 확인 |
| 검색 파일 | `robots.txt`, `sitemap.xml`, `llms.txt` 구문·URL 확인 |
| Lighthouse | Performance 99 · Accessibility 100 · Best Practices 100 · SEO 100 |

## 콘텐츠 출처와 범위

사이트의 내용은 최종 내지 PDF 320쪽에서 확인한 프롤로그, 7개 파트 목차, AI 활용 성숙도 5단계, R-G-C-T-O-R, 21일 훈련 플랜을 바탕으로 구성했습니다. 원본 PDF는 이 저장소에 포함하지 않습니다.

판매처 URL은 확정 정보가 없어 임의로 연결하지 않았습니다. 현재 CTA는 출간·단체 구매·강연·교육 문의로 연결됩니다.

## TROE · 박충효

- [TROE](https://troe.kr)
- [박충효 포트폴리오](https://park.allrounder.im/)
- [LinkedIn](https://www.linkedin.com/in/chunghyopark/)
- 문의: [chunghyo@troe.kr](mailto:chunghyo@troe.kr)

## 저작권

책 표지 이미지, 도서 콘텐츠, TROE·박충효 브랜드 자산의 권리는 각 권리자에게 있습니다. 이 저장소에는 별도의 오픈소스 라이선스가 부여되지 않았으며, 이미지와 콘텐츠의 재배포·상업적 사용은 권리자의 사전 허가가 필요합니다.
