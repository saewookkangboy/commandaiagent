'use strict';
const crypto = require('node:crypto');
const { isIP } = require('node:net');
const POSTS = require('../content/blog/posts.json');
const FUNNEL = require('../content/funnel.json');
const SLUGS = new Set(POSTS.map(post => post.slug));
const ORIGIN = 'https://book.allrounder.im';
const POLICY = '2026-10-14-v1';
const INQUIRIES = new Set(['education', 'workflow', 'undecided']);
const WORK = new Set(['content', 'review', 'performance', 'undecided']);
const LABEL = /^[a-z0-9_-]{1,80}$/;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function validate(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return 'invalid_request';
  if (JSON.stringify(body).length > 12000) return 'invalid_request';
  if (body.website) return 'invalid_request';
  if (!UUID.test(body.submission_id || '')) return 'invalid_request';
  if (typeof body.email !== 'string' || body.email.length > 254 || !/^[^\s@<>\r\n]+@[^\s@<>\r\n]+\.[^\s@<>\r\n]+$/.test(body.email)) return 'email';
  if (!INQUIRIES.has(body.inquiry_type)) return 'inquiry_type';
  if (!WORK.has(body.work_area)) return 'work_area';
  if (body.consent !== true || body.consent_version !== POLICY) return 'consent';
  if (typeof body.organization !== 'string' || body.organization.length > 100) return 'organization';
  if (typeof body.message !== 'string' || body.message.length > 1500) return 'message';
  if (body.source_article_slug && !SLUGS.has(body.source_article_slug)) return 'invalid_request';
  if (!LABEL.test(body.cta_id || 'consulting-direct') || body.ui_variant !== 'ux-v1') return 'invalid_request';
  return null;
}

function backendConfig() {
  if (FUNNEL.policy_approved !== true) return null;
  const url = process.env.SHEETS_WEBAPP_URL || '';
  const secret = process.env.SHEETS_SIGNING_SECRET || '';
  return /^https:\/\/script\.google\.com\/macros\/s\/[a-zA-Z0-9_-]+\/exec$/.test(url) && secret.length >= 32 ? { url, secret } : null;
}

function response(res, status, body) {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.status(status).json(body);
}

async function handler(req, res) {
  const configured = backendConfig();
  if (req.method === 'GET') return response(res, 200, { configured: Boolean(configured), version: POLICY });
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'GET, POST');
    return response(res, 405, { ok: false, error: 'method_not_allowed' });
  }
  const preview = process.env.VERCEL_ENV !== 'production' && process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : null;
  if (![ORIGIN, preview].filter(Boolean).includes(req.headers.origin)) return response(res, 403, { ok: false, error: 'invalid_origin' });
  if (!(req.headers['content-type'] || '').toLowerCase().startsWith('application/json')) return response(res, 415, { ok: false, error: 'invalid_request' });
  if (!configured) return response(res, 503, { ok: false, error: 'unavailable' });
  let body;
  try { body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body; }
  catch (_) { return response(res, 400, { ok: false, error: 'invalid_request' }); }
  const error = validate(body);
  if (error) return response(res, 400, { ok: false, error, field: error });

  // Vercel supplies/overwrites these proxy headers. Never use an empty shared bucket.
  const ip = String(req.headers['x-vercel-forwarded-for'] || req.headers['x-forwarded-for'] || '').split(',')[0].trim();
  if (!isIP(ip)) return response(res, 503, { ok: false, error: 'unavailable' });
  const bucket = crypto.createHmac('sha256', configured.secret).update(new Date().toISOString().slice(0, 10) + ':' + ip).digest('hex');
  const data = {
    submission_id: body.submission_id, email: body.email.trim(), inquiry_type: body.inquiry_type, work_area: body.work_area,
    organization: body.organization.trim(), message: body.message.trim(), source_article_slug: body.source_article_slug || '',
    cta_id: body.cta_id || 'consulting-direct', ui_variant: 'ux-v1', consent_version: POLICY, client_bucket: bucket
  };
  const payload = JSON.stringify(data);
  const timestamp = Date.now();
  const signature = crypto.createHmac('sha256', configured.secret).update(`${timestamp}.${payload}`, 'utf8').digest('hex');
  try {
    const signal = AbortSignal.timeout(22000);
    let upstream = await fetch(configured.url, {
      method: 'POST', headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ timestamp, payload, signature }), redirect: 'manual', signal
    });
    if ([301, 302, 303, 307, 308].includes(upstream.status)) {
      // ContentService returns a one-time Google response URL. Never replay the lead body.
      if (![302, 303].includes(upstream.status)) return response(res, 502, { ok: false, error: 'unavailable' });
      const location = upstream.headers.get('location');
      if (!location) return response(res, 502, { ok: false, error: 'unavailable' });
      const target = new URL(location);
      if (target.protocol !== 'https:' || target.hostname !== 'script.googleusercontent.com' || target.username || target.password) return response(res, 502, { ok: false, error: 'unavailable' });
      upstream = await fetch(target.href, { method: 'GET', redirect: 'manual', signal });
    }
    if (!upstream.ok) return response(res, 502, { ok: false, error: 'unavailable' });
    const result = await upstream.json();
    if (result.ok === true && result.submission_id === data.submission_id) return response(res, 200, { ok: true, duplicate: Boolean(result.duplicate) });
    return response(res, result.error === 'rate_limited' ? 429 : result.error === 'id_conflict' ? 409 : 502, {
      ok: false, error: result.error === 'rate_limited' ? 'rate_limited' : result.error === 'id_conflict' ? 'id_conflict' : 'unavailable'
    });
  } catch (_) { return response(res, 502, { ok: false, error: 'unavailable' }); }
}

module.exports = handler;
module.exports.validate = validate;
module.exports.backendConfig = backendConfig;
