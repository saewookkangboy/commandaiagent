'use strict';
(() => {
  const emit = (name, data) => window.commandAnalytics?.emit(name, data);
  document.querySelectorAll('[data-copy-resource]').forEach(button => button.addEventListener('click', async () => {
    const source = document.getElementById(button.dataset.copyResource);
    if (!source) return;
    try { await navigator.clipboard.writeText(source.textContent); button.textContent = '복사했습니다'; }
    catch (_) { button.textContent = '아래 내용을 선택해 복사하세요'; source.tabIndex = 0; source.focus(); }
  }));
  const form = document.getElementById('consulting-form');
  if (!form || document.body.dataset.policyApproved !== 'true') return;
  const status = document.getElementById('form-status');
  const fallback = document.getElementById('form-unavailable');
  const success = document.getElementById('form-success');
  const submit = form.querySelector('[type="submit"]');
  const labels = { email: '회신 이메일 형식을 확인해주세요.', inquiry_type: '문의 유형을 선택해주세요.', work_area: '관심 업무를 선택해주세요.', consent: '문의 처리에 필요한 개인정보 수집·이용 동의를 확인해주세요.', organization: '소속은 100자 이내로 입력해주세요.', message: '메모는 1,500자 이내로 입력해주세요.' };
  const search = new URLSearchParams(location.search);
  const allowedSlugs = window.commandAnalyticsConfig?.article_slugs || [];
  const slug = allowedSlugs.includes(search.get('from')) ? search.get('from') : '';
  const cta = /^[a-z0-9_-]{1,80}$/.test(search.get('cta') || '') ? search.get('cta') : 'consulting-direct';
  let id = crypto.randomUUID();
  let sending = false;
  let started = false;
  let succeeded = false;
  let fingerprint = '';
  const context = () => ({ form_id: 'team-consulting' });
  for (const [query, field] of [['work', 'work_area'], ['intent', 'inquiry_type']]) {
    const value = search.get(query);
    if (value && [...form.elements[field].options].some(option => option.value === value)) form.elements[field].value = value;
  }
  if (slug) {
    const source = document.getElementById('consulting-source');
    source.hidden = false;
    source.querySelector('a').href = '/blog/' + slug;
  }
  form.addEventListener('focusin', event => {
    if (started || !event.target.matches('input,select,textarea')) return;
    started = true; emit('lead_form_start', context());
  });
  function error(field, message) {
    const input = form.elements[field];
    const region = document.getElementById('error-' + field);
    if (input) input.setAttribute('aria-invalid', 'true');
    if (region) region.textContent = message;
  }
  function resetErrors() {
    form.querySelectorAll('[aria-invalid]').forEach(el => el.removeAttribute('aria-invalid'));
    form.querySelectorAll('.field-error').forEach(el => el.textContent = '');
  }
  form.addEventListener('input', event => {
    const el = event.target;
    if (el.name && el.getAttribute('aria-invalid') === 'true') { el.removeAttribute('aria-invalid'); const region = document.getElementById('error-' + el.name); if (region) region.textContent = ''; }
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (sending || succeeded) return;
    resetErrors();
    const missing = ['email','inquiry_type','work_area','organization','message','consent'].filter(name => !form.elements[name].checkValidity());
    if (missing.length) {
      missing.forEach(name => error(name, labels[name]));
      status.textContent = '표시된 입력 항목을 확인해주세요.';
      form.elements[missing[0]].focus();
      emit('lead_form_error', { ...context(), error_code: 'validation' });
      return;
    }
    const data = Object.fromEntries(new FormData(form));
    const content = { email: data.email.trim(), inquiry_type: data.inquiry_type, work_area: data.work_area, organization: data.organization || '', message: data.message || '', consent: form.elements.consent.checked, consent_version: '2026-10-14-v1', source_article_slug: slug, cta_id: cta, ui_variant: 'ux-v1', website: data.website || '' };
    const current = JSON.stringify(content);
    if (fingerprint && fingerprint !== current) id = crypto.randomUUID();
    fingerprint = current;
    sending = true;
    submit.disabled = true;
    form.setAttribute('aria-busy', 'true');
    status.textContent = '문의 내용을 저장하고 있습니다. 잠시만 기다려주세요.';
    try {
      const result = await fetch('/api/lead', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...content, submission_id: id }), credentials: 'same-origin', signal: AbortSignal.timeout(28000) });
      const body = await result.json();
      if (!result.ok || body.ok !== true) {
        if (body.field && labels[body.field]) error(body.field, labels[body.field]);
        if (body.error === 'id_conflict') id = crypto.randomUUID();
        const code = body.error === 'rate_limited' ? 'rate_limited' : body.field && labels[body.field] ? 'validation' : 'server';
        emit('lead_form_error', { ...context(), error_code: code });
        status.textContent = code === 'rate_limited' ? '요청이 잠시 많습니다. 입력 내용은 유지됩니다. 2분 뒤 다시 제출하거나 아래 이메일로 문의해주세요.' : '저장을 확인하지 못했습니다. 입력 내용은 유지됩니다. 다시 제출하거나 아래 이메일로 문의해주세요.';
        status.focus(); return;
      }
      succeeded = true;
      emit('lead_form_success', context());
      form.hidden = true;
      success.hidden = false;
      success.focus();
    } catch (_) {
      status.textContent = '저장 결과를 확인하지 못했습니다. 입력 내용은 유지됩니다. 다시 제출해도 같은 접수 ID로 중복 저장을 방지합니다.';
      status.focus(); emit('lead_form_error', { ...context(), error_code: 'network' });
    } finally { sending = false; submit.disabled = false; form.removeAttribute('aria-busy'); }
  });
  window.addEventListener('beforeunload', event => { if (sending) { event.preventDefault(); event.returnValue = ''; } });
  // Backend configuration is a prerequisite; absence never turns a click into a lead.
  fetch('/api/lead', { cache: 'no-store', credentials: 'same-origin' }).then(r => r.ok ? r.json() : null).then(info => {
    if (info?.configured === true && info.version === '2026-10-14-v1') { form.hidden = false; fallback.hidden = true; }
  }).catch(() => { /* Keep the real email fallback visible. */ });
})();
