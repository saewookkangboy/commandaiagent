'use strict';
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname,'..');
const handler = require('../api/lead');
const funnel = require('../content/funnel.json');
const secret = 'a'.repeat(64); // Deterministic unit-test key, never production.
const base = () => ({ submission_id:crypto.randomUUID(),email:'qa@example.invalid',inquiry_type:'workflow',work_area:'review',organization:'',message:'',consent:true,consent_version:'2026-10-14-v1',ui_variant:'ux-v1',cta_id:'end-team' });
const hmac = text => crypto.createHmac('sha256',secret).update(text).digest('hex');
const signed = data => {const timestamp=Date.now();const payload=JSON.stringify(data);return {postData:{contents:JSON.stringify({timestamp,payload,signature:hmac(`${timestamp}.${payload}`)})}};};
const rows=[];
const cache = new Map();
const props = new Map([['SHEET_ID','test-sheet'],['SIGNING_SECRET',secret]]);
let locked = false;
const sheet = {
 getLastRow:()=>rows.length+1,
 getRange(row,col,height,width){return {
  createTextFinder(id){return {matchEntireCell(){return this;},findNext(){const index=rows.findIndex(r=>r[1]===id);return index<0?null:{getRow:()=>index+2};}};},
  getValue:()=>rows[row-2]?.[col-1],
  setValues(values){rows[row-2]=values[0];}
 };}
};
const context={
 PropertiesService:{getScriptProperties:()=>({getProperty:key=>props.get(key),setProperties:value=>Object.entries(value).forEach(([k,v])=>props.set(k,v))})},
 Session:{getActiveUser:()=>({getEmail:()=>''})},
 ContentService:{MimeType:{JSON:'json'},createTextOutput:text=>({setMimeType:()=>JSON.parse(text)})},
 SpreadsheetApp:{openById:()=>({getSheetByName:()=>sheet}),flush(){}},
 Utilities:{DigestAlgorithm:{SHA_256:'sha256'},formatDate:()=>new Date().toISOString(),computeHmacSha256Signature:(value,key)=>[...crypto.createHmac('sha256',key).update(value).digest()],computeDigest:(algorithm,value)=>[...crypto.createHash('sha256').update(value).digest()]},
 CacheService:{getScriptCache:()=>({get:key=>cache.get(key),put:(key,value)=>cache.set(key,value)})},
 LockService:{getScriptLock:()=>({tryLock(){assert.equal(locked,false);locked=true;return true;},releaseLock(){locked=false;}})}
};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(root,'apps-script/Code.gs'),'utf8'),context);
const data = {...base(),source_article_slug:'',client_bucket:'b'.repeat(64)};
assert.equal(context.doPost({postData:{contents:'{}'}}).ok,false);
assert.equal(rows.length,0);
assert.equal(context.doPost(signed(data)).ok,true);
assert.equal(rows.length,1);
assert.equal(rows[0].length,13);
assert.equal(context.doPost(signed(data)).duplicate,true);
assert.equal(rows.length,1);
assert.equal(context.doPost(signed({...data,email:'different@example.invalid'})).error,'id_conflict');
const injected={...data,submission_id:crypto.randomUUID(),message:'=IMPORTXML("https://example.invalid","x")'};
assert.equal(context.doPost(signed(injected)).ok,true);
assert.ok(rows[1][6].startsWith("'="));
for(let i=0;i<3;i++)assert.equal(context.doPost(signed({...data,submission_id:crypto.randomUUID()})).ok,true);
assert.equal(context.doPost(signed({...data,submission_id:crypto.randomUUID()})).error,'rate_limited');
assert.equal(locked,false);
assert.equal(context.doGet().ready,true);
assert.throws(()=>context.configureWriter({}),/Not authorized/);
console.log('PASS Apps Script signature, fail-closed, real-save acknowledgment, duplicate/conflict, formula escaping, rate limit, lock release, owner-only setup (memory mocks)');

async function request(body, options={}) {
 let status, result;const headers={};
 const res={setHeader:(k,v)=>headers[k]=v,status(code){status=code;return this;},json(value){result=value;}};
 await handler({method:options.method||'POST',headers:{origin:options.origin||'https://book.allrounder.im','content-type':'application/json'},body},res);
 assert.equal(headers['Cache-Control'],'no-store');
 return {status,result};
}
(async()=>{
 const approved=funnel.policy_approved;const originalFetch=global.fetch;const originalEnv={url:process.env.SHEETS_WEBAPP_URL,key:process.env.SHEETS_SIGNING_SECRET};
 try {
  process.env.SHEETS_WEBAPP_URL='https://script.google.com/macros/s/test-only/exec';process.env.SHEETS_SIGNING_SECRET=secret;
  funnel.policy_approved=false;
  assert.equal((await request(base())).status,503);
  funnel.policy_approved=true;
  assert.equal((await request(base(),{origin:'https://evil.example.invalid'})).status,403);
  assert.equal((await request({...base(),email:'bad'})).status,400);
  assert.equal((await request({...base(),consent:false})).status,400);
  global.fetch=async(url,options)=>{const packet=JSON.parse(options.body);assert.equal(packet.signature,hmac(`${packet.timestamp}.${packet.payload}`));const saved=JSON.parse(packet.payload);assert.ok(!('consent' in saved));assert.match(saved.client_bucket,/^[0-9a-f]{64}$/);return {ok:true,json:async()=>({ok:true,submission_id:saved.submission_id})};};
  assert.equal((await request(base())).result.ok,true);
  global.fetch=async()=>({ok:true,json:async()=>({ok:true,submission_id:'wrong-id'})});
  assert.equal((await request(base())).status,502);
  global.fetch=async()=>{throw Error('network outage');};
  assert.equal((await request(base())).status,502);
  assert.equal((await request(null,{method:'GET'})).result.configured,true);
  console.log('PASS Vercel policy/config gates, origin, validation, signed payload, matching save ID, upstream/network failures (no network)');
 } finally {
  funnel.policy_approved=approved;global.fetch=originalFetch;
  for (const [key,value] of [['SHEETS_WEBAPP_URL',originalEnv.url],['SHEETS_SIGNING_SECRET',originalEnv.key]]) {if(value===undefined)delete process.env[key];else process.env[key]=value;}
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
