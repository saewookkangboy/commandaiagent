'use strict';
(() => {
  const measure = (name, parameters = {}) => window.commandAnalytics?.emit(name, parameters);
  let diagnosisStarted = false;
  const startDiagnosis = (position = 'diagnosis') => {
    if (diagnosisStarted) return;
    diagnosisStarted = true;
    measure('start_situation_diagnosis', { position });
  };
  document.querySelectorAll('[data-diagnosis-start]').forEach(link => {
    link.addEventListener('click', () => startDiagnosis(link.dataset.position || 'hero'));
  });
  const form = document.getElementById('situation-form');
  const status = document.getElementById('situation-status');
  const recommendations = {
    solo: 'SOLO — 반복 업무를 나누는 시작점부터 확인해 보세요.',
    team: 'TEAM — 업무 지시서와 공통 검수 기준부터 확인해 보세요.',
    loop: 'LOOP — 수정·승인·기록을 잇는 3주 훈련부터 확인해 보세요.'
  };
  if (form && status) {
    form.addEventListener('change', event => {
      const value = event.target.value;
      if (!(value in recommendations)) return;
      startDiagnosis();
      status.textContent = recommendations[value];
    });
    form.addEventListener('submit', event => {
      event.preventDefault();
      const selected = form.querySelector('input[name="situation"]:checked');
      if (!selected) { form.reportValidity(); return; }
      const target = document.getElementById(`situation-${selected.value}`);
      if (!target) return;
      startDiagnosis();
      measure('select_solo_team_loop', { situation: selected.value });
      window.location.hash = target.id;
      target.focus({ preventScroll: true });
    });
  }
  document.querySelectorAll('[data-reading-path]').forEach(link => {
    link.addEventListener('click', () => {
      const parts = link.dataset.parts.split(',');
      parts.forEach(number => {
        const part = document.getElementById(`part-${number}`);
        if (part) part.open = true;
      });
      measure('select_reading_path', { situation: link.dataset.readingPath, parts: parts.join(',') });
    });
  });
  const openLinkedPart = () => {
    if (!/^#part-[1-7]$/.test(window.location.hash)) return;
    const target = document.querySelector(window.location.hash);
    if (target) target.open = true;
  };
  window.addEventListener('hashchange', openLinkedPart);
  openLinkedPart();
  document.querySelectorAll('[data-rgctor]').forEach(card => {
    card.addEventListener('toggle', () => {
      if (card.open) measure('open_rgctor_example', { element: card.dataset.rgctor });
    });
  });
  const day1 = document.getElementById('day1-preview');
  if (day1) day1.addEventListener('toggle', () => {
    if (day1.open) measure('open_day1_preview');
    // Individual checkboxes are deliberately neither persisted nor measured.
  });
  document.querySelectorAll('.mobile-menu a').forEach(link => {
    link.addEventListener('click', () => link.closest('details').removeAttribute('open'));
  });
})();
