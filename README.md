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

---

## 프로젝트 소개

이 저장소는 박충효 저 『AI Agent를 지휘하는 마케터』의 핵심 메시지를 웹에서 경험할 수 있도록 만든 반응형 프로모션 사이트입니다.

단순히 AI 도구를 소개하는 대신, 마케터가 목표와 기준을 세우고 AI Agent에게 업무를 맡긴 뒤 최종 결과를 검수하는 **Command Marketing 운영 방식**을 시각적으로 전달합니다. 책 표지의 청록색 인상과 TROE·AX WORKS의 절제된 브랜드 시스템을 하나의 웹 경험으로 연결했습니다.

## 실제 화면

<p align="center">
  <img src="./docs/readme/site-preview.png" width="900" alt="AI Agent를 지휘하는 마케터 프로모션 사이트 데스크톱 전체 화면">
</p>

## 사이트에 담긴 내용

- **AI 활용 성숙도 5단계**: 도구 사용자에서 커맨드 마케터로 이동하는 과정을 인터랙티브 탭으로 탐색합니다.
- **R-G-C-T-O-R**: Role, Goal, Context, Tool, Output, Review로 구성한 AI 업무 지시서 구조를 설명합니다.
- **7개 파트 목차**: AI Agent 리터러시부터 리서치·콘텐츠·광고·CRM·운영 매뉴얼까지 책의 전체 흐름을 아코디언으로 제공합니다.
- **21일 훈련 플랜**: 업무 분해, 지시·검수 기준, 반복 운영의 세 단계 실천 방향을 제안합니다.
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
├── .openai/
│   └── hosting.json
├── docs/
│   └── readme/
│       └── site-preview.png
└── dist/
    ├── index.html
    └── assets/
        ├── book-3d.png
        ├── book-cover.jpg
        └── book-flat.jpg
```

## 디자인 시스템

| 역할 | 색상 | 용도 |
|---|---|---|
| Ink | `#0C1116` | 본문, 다크 섹션, 정보 구조 |
| Cobalt | `#1C51B9` | AX 브랜드 신뢰감과 강조 |
| Gold | `#C8912B` | 포인트와 핵심 메시지 |
| Mist | `#F4F6F8` | 밝은 배경과 여백 |
| Book Teal | 책 표지 기반 청록색 | 도서 정체성과 인터랙션 |

타이포그래피는 별도 웹폰트 의존 없이 시스템 글꼴을 사용하며, 모바일 환경에서는 1열 구조로 자연스럽게 전환됩니다.

## 기술 구성

- HTML, CSS, Vanilla JavaScript 단일 페이지
- 외부 프레임워크와 런타임 의존성 없음
- 반응형 레이아웃과 `prefers-reduced-motion` 대응
- 키보드 접근이 가능한 링크·버튼·아코디언
- Book 스키마 기반 JSON-LD 메타데이터
- 이메일 기반 출간·단체 구매·강연 문의 CTA

## 검수 결과

| 항목 | 결과 |
|---|---|
| 데스크톱 렌더 | 1440 × 1000 전체 화면 확인 |
| 모바일 렌더 | 390 × 844 전체 화면 확인 |
| 가로 오버플로우 | 없음 |
| 브라우저 콘솔 오류 | 0건 |
| 로컬 이미지 누락 | 0건 / 3종 정상 로드 |
| 인터랙션 | 성숙도 탭, PART 07 아코디언 작동 확인 |
| 구조화 데이터 | JSON-LD 파싱 확인 |

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
