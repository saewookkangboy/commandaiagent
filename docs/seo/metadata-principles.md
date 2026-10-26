# 검색 메타데이터 편집 원칙

Google은 `meta name="keywords"`를 색인·순위에 사용하지 않는다. 이 프로젝트의 keywords 메타는 편집 주제를 설명하는 보조 정보이며, 순위 상승을 위한 별도 신호로 취급하지 않는다. 실제 개선의 중심은 글의 검색 의도에 맞는 고유 제목·설명, 사람이 읽는 요약과 주제, 초기 HTML의 본문, 관련 글 연결이다.[1]

Naver는 개별 페이지의 주제를 설명하는 고유 제목과 1~2문장의 설명을 권장하며, 반복·스팸성·무관한 키워드 나열을 피하라고 안내한다. 제목·설명·OG에는 실제 본문과 일치하는 표현만 사용한다. 검색엔진이 검색어와 본문에 따라 표시 문구를 다시 구성할 수 있으므로 작성한 메타가 그대로 노출된다고 보장하지 않는다.[2]

글마다 하나의 대표 검색 의도를 잡고 보조 주제를 4~6개 이내로 제한한다. 실무 가이드와 도서 소개의 목적을 구분한다. 키워드는 검색량 도구에서 측정한 순위가 아니라 기존 원고의 내용·독자 질문을 근거로 선정한다. 검색량·CTR·전환·AI 인용 상승률을 지어내거나 보장하지 않는다.

기존 URL과 canonical, 도서 근거 페이지, 저자/편집 주체의 구분, 썸네일은 보존한다. SEO용 제목은 H1과 같은 주제를 더 간결하게 표현하고, `BlogPosting.headline`은 화면의 H1, `alternativeHeadline`은 검색용 제목과 일치시킨다. `keywords`·`about`·`abstract`의 내용은 보이는 주제·요약과 일치한다. 실제로 제공하지 않는 FAQ·평점·후기·성과 스키마는 추가하지 않는다.

## 주제별 목록의 메타와 사이트맵

목록 검색 제목과 설명은 `content/site.json`의 `blog_title`·`blog_description`에서 관리한다. title과 OG/Twitter는 같은 원본을 사용하며, description은 CollectionPage 설명에도 동기화한다. 최종 제목은 브랜드 접미사 포함30~60자, 설명은50~80자를 이 프로젝트의 편집 검사 범위로 삼는다. 80자는 사용자가 제공한 네이버 URL 검사 권장에 맞춘 범위이며 모든 검색엔진의 절대 규칙은 아니다. 기존홈의 도서명 중심 제목·78자 설명·네이버 소유확인값은 목록의 광범위한 주제로 덮어쓰지 않는다.

다섯 주제는 `sections.json`의 실제 HTML 부분이므로 CollectionPage의 `hasPart`에 WebPageElement로 연결한다. 각 부분의 이름·설명·ItemList 편수·글 순서는 가시 목록과 일치시킨다. `#주제` 주소는 독립 페이지가 아니며 별도 CollectionPage나 sitemap URL로 등록하지 않는다. 별도 카테고리 페이지를 만드는 경우에만 고유 본문·메타·canonical을 제공하는 새 URL을 검토한다.

사이트맵은 기존 색인 대상 정규 HTTPS 주소만 유지하고, 블로그 글 순서를 같은 분류 원본으로 생성한다. Google은 사이트맵 URL 순서를 중요하게 취급하지 않으므로 이 변경을 순위 신호라고 설명하지 않는다. `priority`·`changefreq`도 추가하지 않는다. `lastmod`는 실제 주요 콘텐츠·링크·구조화 데이터 변경일에 대응하고 변경하지 않은 상세 글의 수정일을 일괄 갱신하지 않는다. 대표 이미지·개인정보 noindex/사이트맵 제외·robots의 sitemap 선언을 보존한다.[3]

## References

[1]: https://developers.google.com/search/docs/crawling-indexing/special-tags "Google Search Central — 지원 메타 태그와 meta keywords 비사용"
[2]: https://searchadvisor.naver.com/guide/markup-content "Naver 서치어드바이저 — 제목·설명·오픈그래프 콘텐츠 마크업"
[3]: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap "Google Search Central — 사이트맵 정규 URL·수정일·순서"
