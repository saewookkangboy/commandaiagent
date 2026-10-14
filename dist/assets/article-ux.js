'use strict';

(() => {
  const body = document.body;
  if (!body || body.dataset.pageType !== 'blog_article') return;
  body.dataset.uiVariant = 'ux-v1';

  const media = window.matchMedia?.('(max-width: 760px)');
  const article = document.querySelector('.article-body');
  const bar = document.querySelector('.article-mobile-cta');
  const closeButton = bar?.querySelector('.article-mobile-cta-close');
  if (!media || !article || !bar || !closeButton) return;

  const viewport = window.visualViewport;
  const headings = [...article.querySelectorAll('h2')];
  // The next H2 marks the end of the first core section; all eight articles have one.
  const progressMarker = headings[1] || headings[0];
  const bodyCtas = [...document.querySelectorAll('.article-cta-inline, .article-cta-end')];
  const footer = document.querySelector('.blog-footer');
  const visibleBodyCtas = new Set();
  const hasIntersectionObserver = 'IntersectionObserver' in window;
  let firstSectionPassed = false;
  let dismissed = false;
  let footerVisible = false;
  let hasScrolled = false;
  let frame = 0;

  bar.hidden = true;
  bar.setAttribute('aria-hidden', 'true');

  const viewportHeight = () => viewport?.height || window.innerHeight;
  const keyboardOpen = () => Boolean(viewport && (window.innerHeight - viewport.height > 120));

  function applyBottomSpace(isVisible) {
    const root = document.documentElement;
    root.style.scrollPaddingBottom = isVisible
      ? `${bar.getBoundingClientRect().height + 16}px`
      : '';
  }

  function updateBar() {
    const shouldShow = media.matches
      && hasScrolled
      && firstSectionPassed
      && !dismissed
      && !document.hidden
      && !keyboardOpen()
      && visibleBodyCtas.size === 0
      && !footerVisible;
    bar.hidden = !shouldShow;
    bar.setAttribute('aria-hidden', String(!shouldShow));
    body.classList.toggle('article-mobile-cta-active', shouldShow);
    applyBottomSpace(shouldShow);
  }

  function checkVisibilityFallback() {
    if (hasIntersectionObserver) return;
    const safeBottom = viewportHeight() + 128;
    visibleBodyCtas.clear();
    bodyCtas.forEach(cta => {
      const box = cta.getBoundingClientRect();
      if (box.top < safeBottom && box.bottom > 0) visibleBodyCtas.add(cta);
    });
    if (footer) {
      const box = footer.getBoundingClientRect();
      footerVisible = box.top < viewportHeight() + 80 && box.bottom > 0;
    }
  }

  function assessProgress() {
    frame = 0;
    if (media.matches && hasScrolled && progressMarker) {
      const markerTop = progressMarker.getBoundingClientRect().top;
      if (markerTop <= Math.max(0, document.querySelector('.site-head')?.getBoundingClientRect().bottom || 0) + 16) firstSectionPassed = true;
    }
    checkVisibilityFallback();
    updateBar();
  }

  function requestAssessment() {
    if (!frame) frame = window.requestAnimationFrame(assessProgress);
  }

  function dismiss() {
    const restore = bar.contains(document.activeElement);
    dismissed = true;
    updateBar();
    if (restore) { article.setAttribute('tabindex', '-1'); article.focus({ preventScroll: true }); }
  }

  closeButton.addEventListener('click', dismiss);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !bar.hidden) dismiss();
  });

  window.addEventListener('scroll', () => {
    hasScrolled = true;
    requestAssessment();
  }, { passive: true });
  window.addEventListener('resize', requestAssessment, { passive: true });
  viewport?.addEventListener('resize', updateBar, { passive: true });
  viewport?.addEventListener('scroll', updateBar, { passive: true });
  document.addEventListener('visibilitychange', updateBar);

  const onMediaChange = () => {
    if (!media.matches) {
      bar.hidden = true;
      body.classList.remove('article-mobile-cta-active');
      applyBottomSpace(false);
    }
    requestAssessment();
  };
  if (media.addEventListener) media.addEventListener('change', onMediaChange);
  else media.addListener(onMediaChange);

  if (hasIntersectionObserver) {
    const ctaObserver = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting) visibleBodyCtas.add(entry.target);
        else visibleBodyCtas.delete(entry.target);
      }
      updateBar();
    }, { rootMargin: '0px 0px 128px 0px', threshold: 0.01 });
    bodyCtas.forEach(cta => ctaObserver.observe(cta));

    if (footer) {
      const footerObserver = new IntersectionObserver(entries => {
        footerVisible = entries.some(entry => entry.isIntersecting);
        updateBar();
      }, { rootMargin: '0px 0px 80px 0px', threshold: 0.01 });
      footerObserver.observe(footer);
    }
  }

  // If keyboard or a fixed bar would cover a focused reading control, keep its focus ring visible.
  document.addEventListener('focusin', event => {
    const target = event.target;
    if (!(target instanceof Element) || bar.hidden || bar.contains(target)) return;
    window.requestAnimationFrame(() => {
      if (bar.hidden) return;
      const targetBox = target.getBoundingClientRect();
      const barBox = bar.getBoundingClientRect();
      if (targetBox.bottom > barBox.top || targetBox.top < 0) {
        target.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'auto' });
      }
    });
  });
})();
