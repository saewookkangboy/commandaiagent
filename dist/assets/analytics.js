'use strict';
(() => {
  if (window.commandAnalytics) return;
  const config = window.commandAnalyticsConfig;
  if (!config) return;
  const page = document.body.dataset;
  const pageType = page.pageType || 'not_found';
  const allowed = location.hostname === config.production_host && pageType !== 'not_found';
  window.commandTrackingEnabled = allowed && window.commandTrackingEnabled !== false;
  const enabled = () => allowed && window.commandTrackingEnabled === true;
  const seen = new Set();
  const groups = ['book', 'book_series', 'practical_guide', 'blog_index', 'consulting', 'resources'];
  const slugPattern = /^[a-z0-9_-]{1,80}$/;
  const article = slugPattern.test(page.article || '') ? page.article : '';
  const canonical = document.querySelector('link[rel="canonical"]');
  const canonicalURL = canonical ? new URL(canonical.href) : null;
  const pagePath = canonicalURL && canonicalURL.hostname === config.production_host ? canonicalURL.pathname : '/';
  const context = {
    event_version: config.version,
    page_path: pagePath,
    page_type: pageType,
    content_id: article || (slugPattern.test(page.contentId || '') ? page.contentId : pageType === 'landing' ? 'command_marketing_book' : 'blog_index'),
    ui_variant: page.uiVariant === 'ux-v1' ? 'ux-v1' : 'legacy-v2',
    content_group: groups.includes(page.contentGroup) ? page.contentGroup : 'book'
  };
  if (article) context.article_slug = article;
  if (/^[1-3]$/.test(page.seriesOrder || '')) context.series_order = Number(page.seriesOrder);

  // Format-checked labels from known UTM keys; no form values or arbitrary query keys.
  const campaigns = {};
  const urlParams = new URLSearchParams(location.search);
  const sourceArticle = urlParams.get('from');
  if ((config.article_slugs || []).includes(sourceArticle)) context.source_article_slug = sourceArticle;
  ['source', 'medium', 'campaign', 'content', 'term'].forEach(key => {
    const value = urlParams.get(`utm_${key}`) || '';
    if (/^[\p{L}\p{N}._~-]{1,80}$/u.test(value) && !/^\d{9,15}$/.test(value)) campaigns[`utm_${key}`] = value;
  });

  function clean(key, value) {
    const rule = config.parameters[key];
    if (!rule) return undefined;
    if (rule.enum) return rule.enum.includes(value) ? value : undefined;
    if (rule.type === 'integer') return Number.isInteger(value) && value >= rule.min && value <= rule.max ? value : undefined;
    if (typeof value !== 'string') return undefined;
    if (rule.type === 'label') return slugPattern.test(value) ? value : undefined;
    if (rule.type === 'domain') return /^[a-z0-9.-]{1,80}$/.test(value) ? value : undefined;
    if (rule.type === 'parts') return /^[1-7](,[1-7]){0,6}$/.test(value) ? value : undefined;
    return undefined;
  }

  function emit(name, parameters = {}) {
    if (!enabled() || !Object.prototype.hasOwnProperty.call(config.events, name)) return false;
    const definition = config.events[name];
    const extra = {};
    for (const key of definition.parameters) {
      const value = clean(key, parameters[key]);
      if (value === undefined) return false;
      extra[key] = value;
    }
    for (const key of definition.optional_parameters || []) {
      const value = clean(key, parameters[key]);
      if (value !== undefined) extra[key] = value;
    }
    const onceKey = definition.once ? name : definition.once_by ? `${name}:${extra[definition.once_by]}` : null;
    if (onceKey && seen.has(onceKey)) return false;
    const id = globalThis.crypto?.randomUUID?.() || `cm-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
    const payload = { ...context, ...campaigns, ...extra, funnel_stage: definition.stage, event_id: id };
    let sent = false;
    // One SDK failing must not break the other SDK or the visitor's navigation.
    try {
      if (typeof window.gtag === 'function') { window.gtag('event', name, { ...payload }); sent = true; }
    } catch (_) { /* No payload logging or blocking UI. */ }
    try {
      if (typeof window.fbq === 'function') { window.fbq('trackCustom', name, { ...payload }, { eventID: id }); sent = true; }
    } catch (_) { /* Delivery is independently best-effort. */ }
    if (sent && onceKey) seen.add(onceKey);
    return sent;
  }

  window.commandAnalytics = Object.freeze({ emit, version: config.version });
  if (!enabled()) return;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  const google = document.createElement('script');
  google.async = true;
  google.src = `https://www.googletagmanager.com/gtag/js?id=${config.ga4_id}`;
  document.head.appendChild(google);
  let referrer = '';
  try { referrer = document.referrer ? new URL(document.referrer).origin : ''; } catch (_) { /* Empty referrer. */ }
  const googleConfig = { send_page_view: true, page_location: location.origin + pagePath, page_referrer: referrer, content_group: context.content_group };
  const campaignKeys = { source: 'source', medium: 'medium', campaign: 'name', content: 'content', term: 'term' };
  for (const [key, field] of Object.entries(campaignKeys)) {
    if (campaigns[`utm_${key}`]) googleConfig[`campaign_${field}`] = campaigns[`utm_${key}`];
  }
  try {
    window.gtag('js', new Date());
    window.gtag('config', config.ga4_id, googleConfig);
  } catch (_) { /* Meta and site interactions remain available. */ }

  if (!window.fbq) {
    const fbq = function () { fbq.callMethod ? fbq.callMethod.apply(fbq, arguments) : fbq.queue.push(arguments); };
    fbq.queue = []; fbq.loaded = true; fbq.version = '2.0'; fbq.push = fbq;
    window.fbq = fbq;
    if (!window._fbq) window._fbq = fbq;
    const meta = document.createElement('script');
    meta.async = true;
    meta.src = 'https://connect.facebook.net/en_US/fbevents.js';
    document.head.appendChild(meta);
  }
  try {
    window.fbq('init', config.meta_pixel_id);
    window.fbq('track', 'PageView');
  } catch (_) { /* GA4 and site interactions remain available. */ }

  if ('IntersectionObserver' in window) {
    const timers = new Map();
    const visible = new Set();
    function scheduleCTA(target) {
      if (timers.has(target) || document.hidden || !visible.has(target)) return;
      timers.set(target, setTimeout(() => {
        timers.delete(target);
        if (document.hidden || !visible.has(target) || target.closest('[hidden]')) return;
        const style = getComputedStyle(target);
        if (style.visibility !== 'visible' || Number(style.opacity) === 0) return;
        emit('view_conversion_cta', { cta_id: target.dataset.ctaId, position: target.dataset.position || pageType });
      }, 1000));
    }
    const ctaObserver = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting && entry.intersectionRatio >= 0.5) { visible.add(entry.target); scheduleCTA(entry.target); }
        else { visible.delete(entry.target); clearTimeout(timers.get(entry.target)); timers.delete(entry.target); }
      }
    }, { threshold: [0, 0.5, 1] });
    document.querySelectorAll('[data-cta-id]').forEach(target => ctaObserver.observe(target));
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) { timers.forEach(clearTimeout); timers.clear(); }
      else visible.forEach(scheduleCTA);
    });
    window.addEventListener('pagehide', () => { timers.forEach(clearTimeout); timers.clear(); });
    window.addEventListener('pageshow', () => { if (!document.hidden) visible.forEach(scheduleCTA); });
  }

  function position(link) {
    if (slugPattern.test(link.dataset.position || '')) return link.dataset.position;
    if (link.closest('.series-nav')) return 'series-nav';
    if (link.closest('.article-end')) return 'article-end';
    if (link.closest('.blog-card')) return pageType === 'landing' ? 'landing-blog' : 'blog-card';
    return pageType;
  }

  document.addEventListener('click', event => {
    if (!(event.target instanceof Element)) return;
    const link = event.target.closest('a');
    if (!link || event.defaultPrevented || event.button !== 0) return;
    const cta = link.dataset.cta;
    if (link.dataset.resourceId) {
      emit('resource_access', { resource_id: link.dataset.resourceId, access_type: link.hasAttribute('download') ? 'download' : 'preview', position: position(link) });
    } else if (cta === 'purchase') {
      const destination = new URL(link.href, location.href);
      emit('click_book_purchase', { position: position(link), link_domain: destination.hostname, cta_id: link.dataset.ctaId });
    } else if (link.protocol === 'mailto:') {
      emit('inquiry_start', { position: position(link) });
    } else if (link.hasAttribute('data-consulting-path')) {
      emit('click_consulting_path', { position: position(link), cta_id: link.dataset.ctaId });
    } else if (cta === 'preview' && !link.hasAttribute('data-diagnosis-start')) {
      emit('preview_open', { position: position(link) });
    } else if (link.hasAttribute('data-personal-path')) {
      emit('select_personal_path', { position: position(link) });
    } else {
      const destination = new URL(link.href, location.href);
      const match = destination.pathname.match(/^\/blog\/([a-z0-9_-]+)\/?$/);
      if (destination.origin === location.origin && match) emit('open_blog_article', { article_slug: match[1], position: position(link) });
    }
  });

  document.addEventListener('click', event => {
    if (!(event.target instanceof Element)) return;
    const button = event.target.closest('.maturity-btn');
    if (button) emit('maturity_select', { level: Number(button.dataset.level) + 1 });
  });
  document.addEventListener('keydown', event => {
    if (!(event.target instanceof Element)) return;
    if (!event.target.closest('.maturity-btn') || !['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) return;
    const selected = document.querySelector('.maturity-btn[aria-selected="true"]');
    if (selected) emit('maturity_select', { level: Number(selected.dataset.level) + 1 });
  });
  document.addEventListener('toggle', event => {
    const item = event.target;
    if (!item.open) return;
    if (item.matches('.toc details')) emit('part_expand', { part_number: Number(item.id.replace('part-', '')) });
    if (item.matches('.faq-card')) emit('faq_expand', { question_id: [...document.querySelectorAll('.faq-card')].indexOf(item) + 1 });
  }, true);

  const sections = [...new Set(document.querySelectorAll('[data-track-section],#system,#contents,#faq,#author'))];
  if ('IntersectionObserver' in window) {
    const sectionObserver = new IntersectionObserver(entries => {
      if (document.hidden) return;
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        const section = entry.target.closest('[data-track-section],#system,#contents,#faq,#author');
        if (section) emit('section_view', { section_name: section.dataset.trackSection || section.id });
      }
    }, { threshold: 0.5 });
    sections.forEach(section => sectionObserver.observe(section.querySelector('h2') || section));
  }
  window.addEventListener('scroll', () => {
    if (document.hidden) return;
    const total = document.documentElement.scrollHeight;
    if (total <= innerHeight) return;
    const percent = (scrollY + innerHeight) / total * 100;
    [25, 50, 75, 90].filter(mark => percent >= mark).forEach(mark => emit('scroll_depth', { percent: mark }));
  }, { passive: true });

  let activeMs = 0;
  let tick = performance.now();
  let wasVisible = !document.hidden;
  let reachedEnd = false;
  function checkEngagement() {
    const now = performance.now();
    if (wasVisible) activeMs += Math.max(0, now - tick);
    tick = now;
    wasVisible = !document.hidden;
    if (activeMs < 30000 || document.hidden) return;
    emit('engaged_30s', { active_seconds: 30 });
    if (article && reachedEnd) emit('blog_article_complete', { article_slug: article, active_seconds: 30 });
  }
  document.addEventListener('visibilitychange', checkEngagement);
  let timer = window.setInterval(checkEngagement, 1000);
  window.addEventListener('pagehide', () => {
    checkEngagement();
    window.clearInterval(timer);
    timer = null;
    wasVisible = false;
  });
  window.addEventListener('pageshow', () => {
    if (timer !== null) return;
    tick = performance.now();
    wasVisible = !document.hidden;
    timer = window.setInterval(checkEngagement, 1000);
  });
  if (article) {
    emit('view_blog_article', { article_slug: article });
    const end = document.getElementById('article-end');
    if (end && 'IntersectionObserver' in window) {
      const observer = new IntersectionObserver(entries => {
        if (!document.hidden && entries.some(entry => entry.isIntersecting)) { reachedEnd = true; checkEngagement(); }
      }, { threshold: 0.2 });
      observer.observe(end);
    }
  }
})();
