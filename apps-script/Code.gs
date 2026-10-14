/** Private Google Sheets writer. No lead read/export endpoint. */
const OWNER_EMAIL = 'chunghyo@troe.kr';
const POLICY_VERSION = '2026-10-14-v1';

function json_(value) {
  return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON);
}

function doGet() {
  const props = PropertiesService.getScriptProperties();
  const ready = Boolean(props.getProperty('SHEET_ID') && props.getProperty('SIGNING_SECRET'));
  if (!ready && Session.getActiveUser().getEmail() === OWNER_EMAIL) {
    return HtmlService.createHtmlOutput('<!doctype html><html lang="ko"><meta charset="utf-8"><h1>비공개 문의 저장 설정</h1><p>소유자 전용 일회성 설정입니다. 설정 파일은 공개하지 않습니다.</p><label>서버 설정 JSON <input type="file" id="config" accept="application/json"></label><p id="result" role="status"></p><script>document.getElementById("config").onchange=async function(){try{const c=JSON.parse(await this.files[0].text());google.script.run.withSuccessHandler(function(){document.getElementById("result").textContent="설정이 저장되었습니다. 이 파일을 공유하지 마세요.";}).withFailureHandler(function(){document.getElementById("result").textContent="설정을 저장하지 못했습니다.";}).configureWriter(c);}catch(e){document.getElementById("result").textContent="설정 파일을 확인하세요.";}};</script></html>');
  }
  return json_({ service: 'command-marketing-leads', ready: ready, version: POLICY_VERSION });
}

function configureWriter(config) {
  if (Session.getActiveUser().getEmail() !== OWNER_EMAIL) throw new Error('Not authorized');
  const props = PropertiesService.getScriptProperties();
  if (props.getProperty('SIGNING_SECRET')) throw new Error('Already configured');
  if (!config || !/^[a-zA-Z0-9_-]{20,100}$/.test(config.sheet_id || '') || !/^[0-9a-f]{64}$/.test(config.secret || '')) throw new Error('Invalid config');
  const sheet = SpreadsheetApp.openById(config.sheet_id).getSheetByName('문의접수');
  if (!sheet || sheet.getLastColumn() !== 13 || sheet.getRange(1,2).getValue() !== '접수ID') throw new Error('Invalid sheet');
  props.setProperties({ SHEET_ID: config.sheet_id, SIGNING_SECRET: config.secret });
  return { ok: true };
}

function verifyWriterSetup() {
  if (Session.getActiveUser().getEmail() !== OWNER_EMAIL) throw new Error('Owner authorization required');
  const props = PropertiesService.getScriptProperties();
  const sheet = SpreadsheetApp.openById(props.getProperty('SHEET_ID')).getSheetByName('문의접수');
  if (!sheet || sheet.getLastColumn() !== 13 || sheet.getRange(1,2).getValue() !== '접수ID') throw new Error('Sheet configuration mismatch');
  console.log('Private spreadsheet access and 13-column header verified.');
  return { ready: true };
}

function constantEqual_(left, right) {
  if (typeof right !== 'string' || left.length !== right.length) return false;
  let difference = 0;
  for (let i = 0; i < left.length; i++) difference |= left.charCodeAt(i) ^ right.charCodeAt(i);
  return difference === 0;
}

function hmac_(value, secret) {
  return Utilities.computeHmacSha256Signature(value, secret, Utilities.Charset.UTF_8).map(function(b) { return ('0' + ((b + 256) % 256).toString(16)).slice(-2); }).join('');
}

function digest_(value) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, value, Utilities.Charset.UTF_8).map(function(b) { return ('0' + ((b + 256) % 256).toString(16)).slice(-2); }).join('');
}

function safeCell_(value) {
  const text = String(value || '').replace(/\u0000/g, '');
  return /^[\s]*[=+@-]/.test(text) ? "'" + text : text;
}

function doPost(e) {
  const props = PropertiesService.getScriptProperties();
  const secret = props.getProperty('SIGNING_SECRET');
  if (!secret || !e || !e.postData || e.postData.contents.length > 16000) return json_({ ok: false, error: 'unavailable' });
  let envelope, data;
  try {
    envelope = JSON.parse(e.postData.contents);
    if (!Number.isInteger(envelope.timestamp) || Math.abs(Date.now() - envelope.timestamp) > 300000 || typeof envelope.payload !== 'string' || envelope.payload.length > 12000) return json_({ ok: false, error: 'invalid_request' });
    const signature = hmac_(String(envelope.timestamp) + '.' + envelope.payload, secret);
    if (!constantEqual_(signature, envelope.signature)) return json_({ ok: false, error: 'unauthorized' });
    data = JSON.parse(envelope.payload);
    if (!/^[0-9a-f-]{36}$/.test(data.submission_id || '') || !['education','workflow','undecided'].includes(data.inquiry_type) || !['content','review','performance','undecided'].includes(data.work_area) || data.consent_version !== POLICY_VERSION || typeof data.email !== 'string' || data.email.length > 254 || !/^[^\s@<>\r\n]+@[^\s@<>\r\n]+\.[^\s@<>\r\n]+$/.test(data.email) || typeof data.organization !== 'string' || data.organization.length > 100 || typeof data.message !== 'string' || data.message.length > 1500 || !/^[0-9a-f]{64}$/.test(data.client_bucket || '') || data.ui_variant !== 'ux-v1') return json_({ ok: false, error: 'invalid_request' });
  } catch (error) { return json_({ ok: false, error: 'invalid_request' }); }
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) return json_({ ok: false, error: 'busy' });
  try {
    const sheet = SpreadsheetApp.openById(props.getProperty('SHEET_ID')).getSheetByName('문의접수');
    const rows = sheet.getLastRow();
    if (rows > 1) {
      const existing = sheet.getRange(2,2,rows-1,1).createTextFinder(data.submission_id).matchEntireCell(true).findNext();
      if (existing) {
        const prior = sheet.getRange(existing.getRow(),13).getValue();
        const expected = [data.inquiry_type,data.work_area,data.email,data.organization,data.message,data.source_article_slug || '',data.cta_id || '',data.ui_variant,data.consent_version];
        if (prior !== digest_(JSON.stringify(expected))) return json_({ ok: false, error: 'id_conflict' });
        return json_({ ok: true, duplicate: true, submission_id: data.submission_id });
      }
    }
    const cache = CacheService.getScriptCache();
    const bucket = 'r:' + data.client_bucket;
    const count = Number(cache.get(bucket) || 0);
    const globalCount = Number(cache.get('total') || 0);
    if (count >= 5 || globalCount >= 100) return json_({ ok: false, error: 'rate_limited' });
    const values = [Utilities.formatDate(new Date(),'Asia/Seoul','yyyy-MM-dd HH:mm:ss'),data.submission_id,data.inquiry_type,data.work_area,data.email,data.organization,data.message,data.source_article_slug || '',data.cta_id || '',data.ui_variant,data.consent_version,'신규'].map(safeCell_);
    const fingerprint = digest_(JSON.stringify([data.inquiry_type,data.work_area,data.email,data.organization,data.message,data.source_article_slug || '',data.cta_id || '',data.ui_variant,data.consent_version]));
    sheet.getRange(rows+1,1,1,13).setValues([[...values,fingerprint]]);
    SpreadsheetApp.flush();
    cache.put(bucket,String(count+1),120);
    cache.put('total',String(globalCount+1),60);
    return json_({ ok: true, duplicate: false, submission_id: data.submission_id });
  } catch (error) { return json_({ ok: false, error: 'unavailable' }); }
  finally { lock.releaseLock(); }
}
