import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync, writeFileSync } from 'node:fs';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createInterface } from 'node:readline';
import { randomBytes, createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { run, code } from './workflow-runner.mjs';

const base = new URL('../', import.meta.url);
const workflowFile = new URL('workflows/oke-handoff.json', base);
const mockFile = new URL('tools/mock-store.py', base);
let wf, practice, app;
const processes = [];
const evidence = { scope: 'local Code/expression adapter + real HTTP Mock; not n8n',
  production_api: 'not_run', n8n_auth: 'not_run', official_flow_check: 'not_run' };
const key = randomBytes(24).toString('hex');
const credentials = Object.fromEntries(['WONMIN_PRACTICE_STORE_AUTH', 'WONMIN_APP_STORE_AUTH']
  .map(name => [name, { header: 'X-Api-Key', value: key }]));

async function startStore() {
  const child = spawn('python3', ['-B', fileURLToPath(mockFile), '--port', '0'], {
    env: { ...process.env, INTERNAL_API_KEY: key }, stdio: ['ignore', 'pipe', 'pipe'],
  });
  processes.push(child);
  const lines = createInterface({ input: child.stdout });
  const line = await Promise.race([
    once(lines, 'line').then(([s]) => s),
    once(child, 'exit').then(() => { throw Error('Mock exited before ready'); }),
    new Promise((_, reject) => { const t = setTimeout(() => reject(Error('Mock startup timeout')), 5000); t.unref(); }),
  ]);
  lines.close();
  return `http://127.0.0.1:${JSON.parse(line).port}`;
}
before(async () => {
  assert.ok(existsSync(workflowFile), 'P1-1 workflow must exist');
  assert.ok(existsSync(mockFile), 'C05 HTTP Mock must exist');
  wf = JSON.parse(readFileSync(workflowFile));
  practice = await startStore(); app = await startStore();
});
after(async () => {
  try {
  if (process.env.WONMIN_TEST_REPORT_BASENAME && wf && practice && app) {
    const name = process.env.WONMIN_TEST_REPORT_BASENAME;
    assert.match(name, /^[a-zA-Z0-9_-]+\.json$/);
    evidence.workflow_sha256 = createHash('sha256').update(readFileSync(workflowFile)).digest('hex');
    evidence.mock_sha256 = createHash('sha256').update(readFileSync(mockFile)).digest('hex');
    evidence.test_sha256 = createHash('sha256').update(readFileSync(fileURLToPath(import.meta.url))).digest('hex');
    evidence.created_at = new Date().toISOString();
    evidence.node_version = process.version;
    writeFileSync(new URL('runs/' + name, base), JSON.stringify(evidence, null, 2) + '\n', { flag: 'wx' });
  }
  } finally {
    await Promise.all(processes.map(async p => {
    if (p.exitCode === null) { p.kill(); await once(p, 'exit'); }
    }));
  }
});
const env = (mode = 'practice') => ({ SERVICE_MODE: mode,
  WONMIN_PRACTICE_STORE_URL: practice, WONMIN_APP_STORE_URL: app });
const input = (suffix, extra = {}) => ({ request_id: `p11-${suffix}`, requester: '박서연',
  title: 'VPN 현장 점검 요청', category: 'network', priority: 'normal', reason: 'no_evidence', ...extra });
async function http(url, body, token = key, method = 'POST') {
  const response = await fetch(url, { method, headers: { 'content-type': 'application/json', 'X-Api-Key': token },
    ...(method === 'POST' ? { body: JSON.stringify(body) } : {}) });
  return { status: response.status, body: await response.json() };
}
const ops = url => http(url + '/_mock/ops', null, key, 'GET').then(r => r.body);

test('workflow is inactive, Header Auth protected and has one response node', () => {
  assert.equal(wf.active, false);
  const hook = wf.nodes.find(n => n.type.endsWith('.webhook'));
  assert.equal(hook.parameters.path, 'oke-handoff');
  assert.ok(typeof hook.webhookId === 'string' && hook.webhookId.length > 0,
    'published n8n must register the contract path rather than a workflow-scoped fallback');
  assert.equal(hook.parameters.authentication, 'headerAuth');
  assert.equal(hook.parameters.responseMode, 'responseNode');
  assert.equal(wf.nodes.filter(n => n.type.endsWith('.respondToWebhook')).length, 1);
  for (const node of wf.nodes.filter(n => n.type.endsWith('.httpRequest'))) {
    assert.equal(node.retryOnFail, false);
    assert.equal(node.parameters.options.redirect.redirect.followRedirects, false);
  }
});

test('normal ticket uses C05 key and restores priority absent from store response', async () => {
  const r = await run(wf, input('normal'), env(), credentials);
  assert.equal(r.status, 200);
  assert.deepEqual(r.body, { ok: true, ticket: { ticket_id: r.body.ticket.ticket_id, priority: 'normal', duplicate: false },
    reason: null, alerted: true, dlq: false });
  assert.match(r.body.ticket.ticket_id, /^T-\d+$/);
  const observed = (await ops(practice)).tickets.filter(t => t.ticket_id === r.body.ticket.ticket_id).length;
  assert.equal(observed, 1);
  evidence.normal = { response: r.body, observed_ticket_count: observed };
});
test('high priority is preserved and alert severity is high', async () => {
  const r = await run(wf, input('high', { priority: 'high' }), env(), credentials);
  assert.equal(r.body.ticket.priority, 'high');
  const snapshot = await ops(practice);
  assert.equal(snapshot.alerts.find(a => a.ticket_id === r.body.ticket.ticket_id).severity, 'high');
});
test('sequential same key returns same ticket ID and duplicate=true', async () => {
  const a = await run(wf, input('duplicate'), env(), credentials);
  const b = await run(wf, input('duplicate'), env(), credentials);
  assert.equal(a.body.ticket.duplicate, false);
  assert.equal(b.body.ticket.duplicate, true);
  assert.equal(a.body.ticket.ticket_id, b.body.ticket.ticket_id);
  const observed = (await ops(practice)).tickets.filter(t => t.ticket_id === a.body.ticket.ticket_id).length;
  assert.equal(observed, 1);
  evidence.sequential = { first: a.body, second: b.body, observed_ticket_count: observed };
});
test('eight simultaneous same-key requests create exactly one ticket', async () => {
  const results = await Promise.all(Array.from({ length: 8 }, () => run(wf, input('parallel'), env(), credentials)));
  assert.equal(new Set(results.map(r => r.body.ticket.ticket_id)).size, 1);
  assert.equal(results.filter(r => !r.body.ticket.duplicate).length, 1);
  assert.equal(results.filter(r => r.body.ticket.duplicate).length, 7);
  const observed = (await ops(practice)).tickets.filter(t => t.ticket_id === results[0].body.ticket.ticket_id).length;
  assert.equal(observed, 1);
  evidence.concurrent = { requests: results.length, responses: results.map(r => r.body), observed_ticket_count: observed };
});
test('app mode writes only app store and sends an idempotent alert event_key', async () => {
  const before = await ops(practice);
  const a = await run(wf, input('app'), env('app'), credentials);
  const b = await run(wf, input('app'), env('app'), credentials);
  assert.equal(a.body.ok, true); assert.equal(b.body.alerted, true);
  assert.equal(b.body.ticket.duplicate, true);
  const after = await ops(app);
  assert.equal(after.ticket_count, 1); assert.equal(after.alert_count, 1);
  assert.deepEqual(await ops(practice), before);
  evidence.app_mode_mock = { first: a.body, second: b.body, observed_ticket_count: after.ticket_count,
    observed_alert_count: after.alert_count, practice_unchanged: true };
});
test('payload cannot select app or override store URL', async () => {
  const before = await ops(app);
  const r = await run(wf, input('mode-injection', { SERVICE_MODE: 'app', store_url: app }), env(), credentials);
  assert.equal(r.body.ok, true);
  assert.deepEqual(await ops(app), before);
});
for (const [name, extra] of [
  ['missing request_id', { request_id: null }], ['blank title', { title: ' ' }],
  ['unknown requester', { requester: '없는직원' }], ['invalid priority', { priority: 'critical' }],
  ['non-string reason', { reason: {} }], ['65-char ID', { request_id: 'x'.repeat(65) }],
  ['non-string evidence_summary', { evidence_summary: [] }],
]) {
  test(`invalid C04 ${name} does not call storage`, async () => {
    const before = await ops(practice);
    const r = await run(wf, input('bad', extra), env(), credentials);
    assert.equal(r.status, 400);
    assert.deepEqual(await ops(practice), before);
  });
}
for (const body of [null, [], 'text']) {
  test(`invalid body ${JSON.stringify(body)} does not call storage`, async () => {
    const before = await ops(practice);
    const r = await run(wf, body, env(), credentials);
    assert.equal(r.status, 400); assert.deepEqual(await ops(practice), before);
  });
}
test('64-codepoint request ID is preserved', async () => {
  const id = '가'.repeat(64);
  const r = await run(wf, input('boundary', { request_id: id }), env(), credentials);
  assert.equal(r.body.ok, true);
});
test('unknown mode fails closed without writes or leaking configuration', async () => {
  const before = await ops(practice);
  const r = await run(wf, input('badmode'), env('invalid'), credentials);
  assert.equal(r.status, 503); assert.equal(r.body.ok, false);
  assert.deepEqual(await ops(practice), before);
});
test('validation strips headers, secrets, raw contact and unnecessary evidence before C05', () => {
  const node = wf.nodes.find(n => n.name === 'H02 Validate and Map');
  const marker = 'local-only-sensitive-marker';
  const body = input('safe', { title: `연락 safe@example.invalid 010-1234-5678 password=${marker}`, evidence_summary: marker });
  const r = code(node, { body, headers: { authorization: marker } });
  const text = JSON.stringify(r);
  assert.ok(!text.includes('safe@example.invalid')); assert.ok(!text.includes('010-1234-5678'));
  assert.ok(!text.includes(marker)); assert.ok(!text.includes('authorization'));
  assert.equal(r.ticket_payload.key, body.request_id);
});
for (const bad of [
  { statusCode: 200, body: { ticket_id: 'T-9001', duplicate: 'false' } },
  { statusCode: 201, body: { ticket_id: 'T-9001', duplicate: true } },
  { statusCode: 503, body: { ticket_id: 'T-9001', duplicate: false } },
  { statusCode: 201, body: { ticket_id: '', duplicate: false } },
]) {
  test(`unconfirmed ticket is never reported successful (${JSON.stringify(bad)})`, () => {
    const node = wf.nodes.find(n => n.name === 'H06 Keep Ticket');
    const r = code(node, bad, { 'H03 Select Store': { priority: 'normal', mode: 'practice' }, 'H05 Recheck Budget': { will_retry: false } });
    assert.equal(r.ticket, null);
  });
}
test('alert failure keeps confirmed ticket and does not fabricate ACK', async () => {
  const transport = (url, options) => url.endsWith('/alerts')
    ? Promise.resolve(new Response(JSON.stringify({ stored: 0, count: 0 }), { status: 200 })) : fetch(url, options);
  const r = await run(wf, input('alert-unconfirmed'), env(), credentials, transport);
  assert.ok(r.body.ticket.ticket_id); assert.equal(r.body.alerted, false); assert.equal(r.body.reason, 'alerts_down');
});
test('C05 mock rejects wrong API key with zero writes', async () => {
  const before = await ops(app);
  assert.equal((await http(app + '/tickets', { key: 'noauth' }, 'wrong')).status, 401);
  assert.deepEqual(await ops(app), before);
});
test('C05 mock returns 201 then 200 with no priority response field', async () => {
  const b = { key: 'direct-c05', title: '장비 확인', requester: '한지훈', category: 'device', priority: 'normal' };
  const a = await http(app + '/tickets', b), c = await http(app + '/tickets', b);
  assert.equal(a.status, 201); assert.equal(c.status, 200);
  assert.deepEqual(a.body, { ticket_id: a.body.ticket_id, duplicate: false });
  assert.deepEqual(c.body, { ticket_id: a.body.ticket_id, duplicate: true });
});
test('C05 same key with different owner/body returns 409 without ticket disclosure', async () => {
  const b = { key: 'owner', title: '장비 확인', requester: '한지훈', category: 'device', priority: 'normal' };
  await http(app + '/tickets', b);
  for (const changed of [{ ...b, requester: '박서연' }, { ...b, title: '다른 작업' }]) {
    const r = await http(app + '/tickets', changed);
    assert.equal(r.status, 409); assert.equal(r.body.ticket_id, undefined);
  }
});
test('C05 mock validates before storage and observations omit raw payload and key', async () => {
  const before = await ops(app);
  const r = await http(app + '/tickets', { key: 'invalid', priority: 'critical' });
  assert.equal(r.status, 400); assert.deepEqual(await ops(app), before);
  const text = JSON.stringify(await ops(app));
  assert.ok(!text.includes('VPN 현장')); assert.ok(!text.includes(key)); assert.ok(!text.includes('박서연'));
});

test('store selection works without URL global or external modules', () => {
  const node = wf.nodes.find(n => n.name === 'H03 Select Store');
  const r = code(node, {}, {}, { SERVICE_MODE: 'practice' });
  assert.equal(r.ready, true); assert.equal(r.base_url, 'http://data-api:8800');
});
for (const url of ['http://user:secret@localhost:18800', 'http://localhost:18800/tickets',
  'http://localhost:18800?token=secret', 'file:///tmp/store', 'http://localhost:99999']) {
  test(`deployment URL is rejected safely: ${url.replace('secret', '[redacted]')}`, async () => {
    const before = await ops(practice);
    const r = await run(wf, input('bad-url'), { ...env(), WONMIN_PRACTICE_STORE_URL: url }, credentials);
    assert.equal(r.status, 503); assert.deepEqual(await ops(practice), before);
    assert.ok(!JSON.stringify(r.body).includes('secret'));
  });
}
test('ticket HTTP failure returns unconfirmed ticket and no invented storage success', async () => {
  const transport = async () => { throw Error('never expose this transport detail'); };
  const r = await run(wf, input('transport'), env(), credentials, transport);
  assert.deepEqual(r.body, { ok: false, ticket: null, reason: 'tickets_down', alerted: false, dlq: false });
  assert.equal(r.status, 200);
});
for (const ack of [{ stored: true, count: 1 }, { stored: 1, count: '1' }, { stored: 0, count: 1 }]) {
  test(`invalid alert ACK does not become success: ${JSON.stringify(ack)}`, async () => {
    const transport = (url, options) => url.endsWith('/alerts')
      ? Promise.resolve(new Response(JSON.stringify(ack), { status: 200 })) : fetch(url, options);
    const r = await run(wf, input('ack-' + JSON.stringify(ack)), env(), credentials, transport);
    assert.ok(r.body.ticket); assert.equal(r.body.alerted, false); assert.equal(r.body.reason, 'alerts_down');
  });
}
test('C05 parallel HTTP calls themselves enforce atomic 201/200 semantics', async () => {
  const b = { key: 'direct-parallel', title: '장비 확인', requester: '한지훈', category: 'device', priority: 'normal' };
  const replies = await Promise.all(Array.from({ length: 8 }, () => http(app + '/tickets', b)));
  assert.equal(replies.filter(r => r.status === 201).length, 1);
  assert.equal(replies.filter(r => r.status === 200 && r.body.duplicate).length, 7);
  assert.equal(new Set(replies.map(r => r.body.ticket_id)).size, 1);
});
