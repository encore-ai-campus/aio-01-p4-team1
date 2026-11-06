// Review no-key/keyed alert semantics using a private ephemeral HTTP Mock.
// No real data-api, PostgreSQL, or n8n calls.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createInterface } from 'node:readline';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash, randomBytes } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { run, code } from '../tests/workflow-runner.mjs';

const own = new URL('../', import.meta.url);
const read = relative => readFileSync(new URL(relative, own));
const handoff = JSON.parse(read('workflows/oke-handoff.json'));
const errors = JSON.parse(read('workflows/oke-errors.json'));
const key = randomBytes(24).toString('hex');
const child = spawn('python3', ['-B', fileURLToPath(new URL('tools/mock-store.py', own)), '--port', '0'], {
  env: { ...process.env, INTERNAL_API_KEY: key, WONMIN_MOCK_FAULTS: '{}' }, stdio: ['ignore', 'pipe', 'pipe'],
});
try {
  const lines = createInterface({ input: child.stdout });
  const line = await Promise.race([
    once(lines, 'line').then(([line]) => line),
    once(child, 'exit').then(() => { throw Error('Mock failed to start'); }),
    new Promise((_, reject) => { const t = setTimeout(() => reject(Error('Mock startup timeout')), 5000); t.unref(); }),
  ]);
  lines.close();
  const url = `http://127.0.0.1:${JSON.parse(line).port}`;
  const headers = { 'X-Api-Key': key, 'content-type': 'application/json' };
  const payload = { workflow: 'oke-handoff', node: 'C05 ACK review', message: '합성 알림 확인', severity: 'normal' };
  const send = async body => {
    const response = await fetch(url + '/alerts', { method: 'POST', headers, body: JSON.stringify(body) });
    assert.equal(response.status, 200);
    return response.json();
  };
  const ops = async () => {
    const response = await fetch(url + '/_mock/ops', { headers });
    assert.equal(response.status, 200);
    return response.json();
  };
  const observations = [];
  const noKey = [await send(payload), await send(payload)];
  assert.deepEqual(noKey, [{ stored: 1, count: 1, duplicate: false }, { stored: 1, count: 2, duplicate: false }]);
  observations.push({ scenario: 'no_key_sequential_2', request: payload, responses: noKey, stored_alerts: 2 });
  const noKeyParallel = await Promise.all(Array.from({ length: 8 }, () => send(payload)));
  assert.ok(noKeyParallel.every(r => r.stored === 1 && r.duplicate === false));
  assert.deepEqual(noKeyParallel.map(r => r.count).sort((a, b) => a - b), [3, 4, 5, 6, 7, 8, 9, 10]);
  observations.push({ scenario: 'no_key_parallel_8', responses: noKeyParallel, observed_alert_count: (await ops()).alert_count });
  const nullKey = [await send({ ...payload, event_key: null }), await send({ ...payload, event_key: null })];
  assert.deepEqual(nullKey, [{ stored: 1, count: 11, duplicate: false }, { stored: 1, count: 12, duplicate: false }]);
  observations.push({ scenario: 'null_key_sequential_2', responses: nullKey });
  const keyed = { ...payload, event_key: 'wm-ack-review:ticket-created' };
  const keyedSequential = [await send(keyed), await send(keyed)];
  assert.deepEqual(keyedSequential, [{ stored: 1, count: 13, duplicate: false }, { stored: 0, count: 13, duplicate: true }]);
  observations.push({ scenario: 'keyed_sequential_2', request: keyed, responses: keyedSequential });
  const keyedParallel = await Promise.all(Array.from({ length: 8 }, () => send(keyed)));
  assert.ok(keyedParallel.every(r => r.stored === 0 && r.duplicate === true && r.count === 13));
  observations.push({ scenario: 'existing_key_parallel_8', responses: keyedParallel, observed_alert_count: (await ops()).alert_count });

  const env = { SERVICE_MODE: 'practice', WONMIN_PRACTICE_STORE_URL: url, WONMIN_APP_STORE_URL: url };
  const credentials = Object.fromEntries(['WONMIN_PRACTICE_STORE_AUTH', 'WONMIN_APP_STORE_AUTH']
    .map(name => [name, { header: 'X-Api-Key', value: key }]));
  const body = { request_id: 'wm-ack-review-ticket', requester: '박서연', title: 'VPN 점검',
    category: 'network', priority: 'normal', reason: 'no_evidence' };
  const first = await run(handoff, body, env, credentials);
  const repeated = await run(handoff, body, env, credentials);
  assert.equal(first.history['H07 Failure Context'].alert_payload.event_key, undefined);
  assert.equal(repeated.history['H07 Failure Context'].alert_payload.event_key, undefined);
  assert.equal(repeated.body.ticket.duplicate, true);
  assert.equal(first.body.ticket.ticket_id, repeated.body.ticket.ticket_id);
  assert.equal(first.body.alerted, true); assert.equal(repeated.body.alerted, true);
  const practice = await ops();
  assert.equal(practice.ticket_count, 1); assert.equal(practice.alert_count, 15);
  observations.push({ scenario: 'practice_same_ticket_twice', outgoing_alert: first.history['H07 Failure Context'].alert_payload,
    responses: [first.body, repeated.body], alert_acks: [first.history['H08 Store Alert Practice'], repeated.history['H08 Store Alert Practice']]
      .map(r => ({ http_status: r.statusCode, body: r.body })),
    ticket_count: practice.ticket_count, alerts_added: practice.alert_count - 13 });

  const errorItem = { workflow: { name: 'oke-handoff' }, trigger: { error: { message: '고정 비민감 시험 오류' } } };
  const e1 = await run(errors, errorItem, { ...env, SERVICE_MODE: 'app' }, credentials);
  const e2 = await run(errors, errorItem, { ...env, SERVICE_MODE: 'app' }, credentials);
  assert.equal(e1.history['E02 Select Store'].alert_payload.event_key, undefined);
  assert.equal(e2.history['E02 Select Store'].alert_payload.event_key, undefined);
  assert.equal((await ops()).alert_count, 17);
  observations.push({ scenario: 'errors_missing_parent_id_twice', event_key: 'omitted', outcomes: [e1.body, e2.body], alerts_added: 2 });

  const ackCases = [
    { body: { stored: 1, count: 1 }, mode: 'practice', accepted: true },
    { body: { stored: 1, count: 1, duplicate: false }, mode: 'practice', accepted: true },
    { body: { count: 1 }, mode: 'practice', accepted: false },
    { body: { stored: 0, count: 1 }, mode: 'practice', accepted: false },
    { body: { stored: '1', count: 1 }, mode: 'practice', accepted: false },
    { body: { stored: 0, count: 1, duplicate: true }, mode: 'app', accepted: true },
    { body: { stored: 0, count: 1, duplicate: true }, mode: 'practice', accepted: false },
  ];
  for (const probe of ackCases) {
    const h = code(handoff.nodes.find(n => n.name === 'H08 Check Alert'), { statusCode: 200, body: probe.body },
      { 'H07 Failure Context': { mode: probe.mode, ticket: null, attempts: 1, request_id: 'wm-ack-probe' } });
    const e = code(errors.nodes.find(n => n.name === 'E03 Check Alert'), { statusCode: 200, body: probe.body },
      { 'E02 Select Store': { mode: probe.mode, alert_payload: {} } });
    assert.equal(h.alerted, probe.accepted); assert.equal(e.alerted, probe.accepted);
  }
  observations.push({ scenario: 'legacy_and_keyed_ack_consumer_matrix', synthetic_probes: ackCases });
  const source_sha256 = Object.fromEntries(['workflows/oke-handoff.json', 'workflows/oke-errors.json', 'tools/mock-store.py']
    .map(path => [path, createHash('sha256').update(read(path)).digest('hex')]));
  const report = { scope: 'own ephemeral HTTP Mock + local Code adapter; actual practice data-api/PG/n8n not run',
    created_at: new Date().toISOString(), source_sha256, observations,
    final_observed: await ops(), actual_practice_data_api: 'unverified', actual_jihye_DB: 'not_run' };
  if (process.argv.length === 4 && process.argv[2] === '--output') {
    const name = process.argv[3]; assert.match(name, /^[a-zA-Z0-9_-]+\.json$/);
    writeFileSync(new URL('runs/' + name, own), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
    console.log('Report: develop/wonmin/runs/' + name);
  } else {
    assert.equal(process.argv.length, 2, 'Use --output NEW_BASENAME.json or no arguments');
    console.log(JSON.stringify(report, null, 2));
  }
  console.error('8 alert ACK review groups passed; real practice data-api remains unverified');
} finally {
  if (child.exitCode === null) { child.kill(); await once(child, 'exit'); }
}
