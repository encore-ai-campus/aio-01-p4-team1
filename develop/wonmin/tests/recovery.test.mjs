import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createInterface } from 'node:readline';
import { randomBytes, createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { run, code } from './workflow-runner.mjs';

const own = new URL('../', import.meta.url);
const workflowBytes = readFileSync(new URL('workflows/oke-handoff.json', own));
const wf = JSON.parse(workflowBytes);
const results = [];
const request = suffix => ({ request_id: 'wm-p12-' + suffix, requester: '박서연',
  title: 'VPN 오류 safe@example.invalid 010-1234-5678 password=private-marker',
  category: 'network', priority: 'normal', reason: 'no_evidence', evidence_summary: 'private-marker' });

async function scenario(name, faults, verify, options = {}) {
  const key = randomBytes(24).toString('hex');
  const child = spawn('python3', ['-B', fileURLToPath(new URL('tools/mock-store.py', own)), '--port', '0'], {
    env: { ...process.env, INTERNAL_API_KEY: key, WONMIN_MOCK_FAULTS: JSON.stringify(faults) },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  try {
    const lines = createInterface({ input: child.stdout });
    const ready = await Promise.race([
      once(lines, 'line').then(([line]) => JSON.parse(line)),
      once(child, 'exit').then(() => { throw Error('Mock failed to start'); }),
      new Promise((_, reject) => { const timer = setTimeout(() => reject(Error('Mock startup timeout')), 5000); timer.unref(); }),
    ]);
    lines.close();
    const url = `http://127.0.0.1:${ready.port}`;
    const env = { SERVICE_MODE: options.mode ?? 'practice', WONMIN_PRACTICE_STORE_URL: url,
      WONMIN_APP_STORE_URL: url, WONMIN_RETRY_WAIT_MS: '0' };
    const credentials = Object.fromEntries(['WONMIN_PRACTICE_STORE_AUTH', 'WONMIN_APP_STORE_AUTH']
      .map(n => [n, { header: 'X-Api-Key', value: key }]));
    const call = () => run(wf, request(name), env, credentials);
    const ops = async () => {
      const response = await fetch(url + '/_mock/ops', { headers: { 'X-Api-Key': key } });
      assert.equal(response.status, 200);
      return response.json();
    };
    const started = performance.now();
    const first = await call();
    let snapshot = await ops();
    await verify(first, snapshot, { call, ops });
    if (options.settleMs) {
      await new Promise(resolve => setTimeout(resolve, options.settleMs));
      snapshot = await ops();
      assert.equal(snapshot.ticket_count, 1, 'late commit and retry still keep one ticket');
    }
    const text = JSON.stringify({ response: first.body, snapshot });
    for (const marker of [key, 'safe@example.invalid', '010-1234-5678', 'private-marker', '박서연']) {
      assert.ok(!text.includes(marker), 'recovery report must not expose private input/credentials');
    }
    results.push({ scenario: name, faults, mode: env.SERVICE_MODE,
      response: first.body, observed: snapshot, final_observed: await ops(), elapsed_ms: Math.round(performance.now() - started) });
  } finally {
    if (child.exitCode === null) { child.kill(); await once(child, 'exit'); }
  }
}
const failed = (alerted, dlq) => ({ ok: false, ticket: null, reason: 'tickets_down', alerted, dlq });

for (const [name, faults, alerted, dlq] of [
  ['tickets_down', { tickets: [{ status: 503 }] }, true, true],
  ['ticket_alert_down', { tickets: [{ status: 503 }], alerts: [{ status: 503 }] }, false, true],
  ['ticket_dlq_down', { tickets: [{ status: 503 }], dlq: [{ status: 503 }] }, true, false],
  ['all_down', { tickets: [{ status: 503 }], alerts: [{ status: 503 }], dlq: [{ status: 503 }] }, false, false],
]) {
  test(`P1-2 independent sinks: ${name}`, () => scenario(name, faults, (r, s) => {
    assert.equal(r.status, 200);
    assert.deepEqual(r.body, failed(alerted, dlq));
    assert.deepEqual(s.calls, { tickets: 2, alerts: 1, dlq: 1 });
    assert.equal(s.ticket_count, 0);
    assert.equal(s.alert_count, Number(alerted)); assert.equal(s.dlq_count, Number(dlq));
  }));
}
for (const status of [400, 401, 403, 404, 409]) {
  test(`P1-2 permanent ticket ${status} has no retry`, () => scenario('permanent-' + status,
    { tickets: [{ status }] }, (r, s) => {
      assert.deepEqual(r.body, failed(true, true));
      assert.deepEqual(s.calls, { tickets: 1, alerts: 1, dlq: 1 });
    }));
}
test('P1-2 transient 503 retries same key/payload once then succeeds', () => scenario('retry-success',
  { tickets: [{ status: 503 }, {}] }, (r, s) => {
    assert.equal(r.body.ok, true); assert.equal(r.body.dlq, false);
    assert.deepEqual(s.calls, { tickets: 2, alerts: 1, dlq: 0 });
    assert.equal(s.ticket_count, 1);
    const attempts = s.attempts.filter(a => a.endpoint === 'tickets');
    assert.equal(new Set(attempts.map(a => a.payload_hash)).size, 1);
    assert.equal(new Set(attempts.map(a => a.key_hash)).size, 1);
  }));
test('P1-2 429 Retry-After zero permits a bounded retry', () => scenario('429-zero',
  { tickets: [{ status: 429, retry_after: '0' }, {}] }, (r, s) => {
    assert.equal(r.body.ok, true); assert.equal(s.calls.tickets, 2);
  }));
for (const value of ['5', 'invalid', '-1']) {
  test(`P1-2 429 Retry-After ${value} skips retry`, () => scenario('429-' + value,
    { tickets: [{ status: 429, retry_after: value }] }, (r, s) => {
      assert.deepEqual(r.body, failed(true, true)); assert.equal(s.calls.tickets, 1);
    }));
}
for (const dlqDown of [false, true]) {
  test(`P1-2 alerts_down keeps ticket; DLQ failure=${dlqDown}`, () => scenario('alerts-' + dlqDown,
    { alerts: [{ status: 503 }], ...(dlqDown ? { dlq: [{ status: 503 }] } : {}) }, (r, s) => {
      assert.equal(r.body.ok, false); assert.equal(r.body.reason, 'alerts_down');
      assert.equal(r.body.alerted, false); assert.equal(r.body.dlq, !dlqDown);
      assert.ok(r.body.ticket.ticket_id); assert.equal(s.ticket_count, 1);
      assert.deepEqual(s.calls, { tickets: 1, alerts: 1, dlq: 1 });
      if (!dlqDown) { assert.equal(s.dlqs[0].safe_payload.stage, 'alert'); assert.equal(s.dlqs[0].safe_payload.ticket_id, r.body.ticket.ticket_id); }
    }));
}
test('P1-2 app duplicate ACK confirms alert without adding a new alert', () => scenario('app-duplicate', {},
  async (r, s, { call, ops }) => {
    assert.equal(r.body.alerted, true);
    const again = await call(); const after = await ops();
    assert.equal(again.body.ticket.duplicate, true); assert.equal(again.body.alerted, true);
    assert.equal(after.alert_count, 1); assert.equal(after.dlq_count, 0);
  }, { mode: 'app' }));
test('P1-2 approved DLQ returns HTTP200 stored/count', () => scenario('dlq200',
  { tickets: [{ status: 503 }] }, (r, s) => {
    assert.equal(r.body.dlq, true); assert.equal(s.dlq_count, 1);
    assert.equal(s.dlqs[0].safe_payload.stage, 'ticket');
    assert.equal(s.dlqs[0].safe_payload.attempts, 2);
  }, { mode: 'app' }));
for (const endpoint of ['alerts', 'dlq']) {
  test(`P1-2 ${endpoint} timeout cannot block the other sink`, () => scenario('timeout-' + endpoint,
    { tickets: [{ status: 503 }], [endpoint]: [{ delay_ms: 800 }] }, (r, s) => {
      assert.equal(r.body.alerted, endpoint !== 'alerts');
      assert.equal(r.body.dlq, endpoint !== 'dlq');
      assert.equal(s.calls.alerts, 1); assert.equal(s.calls.dlq, 1);
    }));
}
test('P1-2 ticket timeout followed by late commit remains idempotent', () => scenario('late-commit',
  { tickets: [{ delay_ms: 1200 }, {}] }, (r, s) => {
    assert.equal(r.body.ok, true); assert.equal(s.ticket_count, 1); assert.equal(s.calls.tickets, 2);
  }, { settleMs: 350 }));
test('P1-2 both ticket timeouts report uncertainty; late completion and same-key replay keep one ticket', () => scenario('both-timeout',
  { tickets: [{ delay_ms: 1500 }, { delay_ms: 1500 }, {}] }, async (r, s, { call, ops }) => {
    assert.deepEqual(r.body, failed(true, true));
    assert.equal(s.calls.tickets, 2);
    await new Promise(resolve => setTimeout(resolve, 650));
    const again = await call();
    assert.equal(again.body.ok, true); assert.equal(again.body.ticket.duplicate, true);
    assert.equal((await ops()).ticket_count, 1);
  }));
test('P1-2 delayed Wait cannot start a retry after the remaining budget is exhausted', () => {
  const gate = wf.nodes.find(n => n.name === 'H05 Recheck Budget');
  assert.ok(gate);
  const r = code(gate, { will_retry: true, deadline_at: Date.now() - 1 });
  assert.equal(r.will_retry, false);
});
test('P1-2 retry gate reserves sink budget and never echoes arbitrary error text', () => {
  const gate = wf.nodes.find(n => n.name === 'H05 Retry Gate');
  assert.ok(gate, 'explicit bounded retry gate required');
  const state = { request_id: 'budget', mode: 'app', base_url: 'http://backend:8000',
    priority: 'normal', ticket_payload: {}, deadline_at: Date.now() + 100, retry_wait_ms: 0 };
  const result = code(gate, { statusCode: 503, body: { password: 'private-marker' } }, { 'H03 Select Store': state });
  assert.equal(result.will_retry, false); assert.ok(!JSON.stringify(result).includes('private-marker'));
});
test('P1-2 DLQ HTTP201 or malformed ACK cannot be counted as success', () => {
  const node = wf.nodes.find(n => n.name === 'H09 Check DLQ');
  assert.ok(node, 'DLQ ACK validator required');
  for (const reply of [{ statusCode: 201, body: { stored: 1, count: 1 } },
    { statusCode: 200, body: { stored: true, count: 1 } }, { statusCode: 200, body: { stored: 1, count: '1' } }]) {
    const result = code(node, reply, { 'H08 Check Alert': { ticket: null, alerted: false } });
    assert.equal(result.dlq, false);
  }
});
after(() => {
  if (!process.env.WONMIN_RECOVERY_REPORT_BASENAME) return;
  const name = process.env.WONMIN_RECOVERY_REPORT_BASENAME;
  assert.match(name, /^[a-zA-Z0-9_-]+\.json$/);
  const hash = bytes => createHash('sha256').update(bytes).digest('hex');
  writeFileSync(new URL('runs/' + name, own), JSON.stringify({
    scope: 'P1-2 local JSON adapter + real fault-injected HTTP Mock; not n8n/backend',
    created_at: new Date().toISOString(), workflow_sha256: hash(workflowBytes),
    mock_sha256: hash(readFileSync(new URL('tools/mock-store.py', own))),
    test_sha256: hash(readFileSync(fileURLToPath(import.meta.url))),
    adapter_sha256: hash(readFileSync(new URL('./workflow-runner.mjs', import.meta.url))),
    node_version: process.version, observations: results,
    actual_n8n: 'not_run', actual_backend_DB: 'not_run',
  }, null, 2) + '\n', { flag: 'wx' });
});
