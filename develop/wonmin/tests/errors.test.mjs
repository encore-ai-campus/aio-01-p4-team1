import { test, after } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createInterface } from 'node:readline';
import { randomBytes, createHash } from 'node:crypto';
import { readFileSync, existsSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { run, code } from './workflow-runner.mjs';

const own = new URL('../', import.meta.url);
const file = new URL('workflows/oke-errors.json', own);
const observations = [];
const workflow = () => {
  assert.ok(existsSync(file), 'P1-3 Error Trigger workflow required');
  return JSON.parse(readFileSync(file));
};
const event = () => ({ workflow: { id: 'parent-1', name: 'oke-handoff' },
  execution: { id: '231', url: 'https://example.invalid/executions/231?token=private-marker',
    error: { message: 'private-marker safe@example.invalid 010-1234-5678', stack: 'private-stack' },
    lastNodeExecuted: 'H04 Create Ticket Practice', mode: 'webhook' },
  request_id: 'unverified-private-marker', headers: { authorization: 'private-marker' } });

async function scenario(name, faults, verify, options = {}) {
  const wf = workflow();
  const key = randomBytes(24).toString('hex');
  const child = spawn('python3', ['-B', fileURLToPath(new URL('tools/mock-store.py', own)), '--port', '0'], {
    env: { ...process.env, INTERNAL_API_KEY: key, WONMIN_MOCK_FAULTS: JSON.stringify(faults) },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  try {
    const lines = createInterface({ input: child.stdout });
    const ready = await Promise.race([
      once(lines, 'line').then(([line]) => JSON.parse(line)),
      once(child, 'exit').then(() => { throw Error('Mock startup failed'); }),
      new Promise((_, reject) => { const t = setTimeout(() => reject(Error('Mock startup timeout')), 5000); t.unref(); }),
    ]);
    lines.close();
    const url = `http://127.0.0.1:${ready.port}`;
    const env = { SERVICE_MODE: options.mode ?? 'app', WONMIN_APP_STORE_URL: url, WONMIN_PRACTICE_STORE_URL: url };
    if (options.url) env.WONMIN_APP_STORE_URL = options.url;
    const credentials = Object.fromEntries(['WONMIN_PRACTICE_STORE_AUTH', 'WONMIN_APP_STORE_AUTH']
      .map(name => [name, { header: 'X-Api-Key', value: options.wrongKey ? 'invalid' : key }]));
    if (options.workflowId) wf.id = options.workflowId;
    const input = options.input === undefined ? event() : options.input;
    const call = () => run(wf, input, env, credentials);
    const result = await call();
    const response = await fetch(url + '/_mock/ops', { headers: { 'X-Api-Key': key } });
    const snapshot = await response.json();
    await verify(result, snapshot, { call, wf });
    for (const node of ['E02 Safe Error Context', 'E02 Select Store', 'E03 Check Alert', 'E04 Check DLQ', 'E05 Outcome']) {
      const safe = JSON.stringify(result.history[node] ?? {});
      for (const marker of [key, 'private-marker', 'private-stack', 'safe@example.invalid', '010-1234-5678', 'authorization']) {
        assert.ok(!safe.includes(marker), 'sensitive fields cannot leave sanitized Code nodes');
      }
    }
    observations.push({ scenario: name, mode: env.SERVICE_MODE, faults,
      outcome: result.body, safe_alert_request: result.history['E02 Select Store']?.alert_payload ?? null,
      safe_dlq_request: result.history['E02 Select Store']?.dlq_payload ?? null,
      observed: snapshot, trace: result.trace });
  } finally {
    if (child.exitCode === null) { child.kill(); await once(child, 'exit'); }
  }
}
test('P1-3 graph is Error Trigger only, inactive, no HTTP response or explicit self-errorWorkflow', () => {
  const wf = workflow();
  assert.equal(wf.active, false);
  assert.equal(wf.nodes.filter(n => n.type.endsWith('.errorTrigger')).length, 1);
  assert.equal(wf.nodes.filter(n => n.type.endsWith('.webhook') || n.type.endsWith('.respondToWebhook')).length, 0);
  assert.ok(!wf.settings.errorWorkflow);
  assert.equal(wf.nodes.filter(n => n.type.endsWith('.stopAndError')).length, 0);
  assert.equal(wf.settings.saveDataErrorExecution, 'none');
  assert.equal(wf.settings.saveDataSuccessExecution, 'none');
  for (const node of wf.nodes.filter(n => n.type.endsWith('.httpRequest'))) {
    assert.equal(node.retryOnFail, false); assert.equal(node.onError, 'continueRegularOutput');
    assert.equal(node.parameters.options.timeout, 600);
  }
});
for (const [name, faults, alerted, dlq, outcome] of [
  ['both_ok', {}, true, true, 'success'],
  ['alert_down', { alerts: [{ status: 503 }] }, false, true, 'partial_failure'],
  ['dlq_down', { dlq: [{ status: 503 }] }, true, false, 'partial_failure'],
  ['both_down', { alerts: [{ status: 503 }], dlq: [{ status: 503 }] }, false, false, 'failed'],
]) {
  test('P1-3 independent sinks: ' + name, () => scenario(name, faults, (r, s) => {
    assert.equal(r.body.outcome, outcome); assert.equal(r.body.alerted, alerted); assert.equal(r.body.dlq, dlq);
    assert.equal(r.body.request_id, null); assert.equal(r.body.execution_ref, '231');
    assert.match(r.history['E02 Select Store'].alert_payload.message, /231/, 'alert-only recovery must keep a safe parent reference');
    assert.deepEqual(s.calls, { tickets: 0, alerts: 1, dlq: 1 });
    assert.equal(s.alert_count, Number(alerted)); assert.equal(s.dlq_count, Number(dlq));
    if (dlq) { assert.equal(s.dlqs[0].safe_payload.stage, 'unexpected'); assert.equal(s.dlqs[0].execution_ref, '231'); }
    assert.equal(r.status, undefined, 'Error workflow must not manufacture a parent HTTP response');
  }));
}
for (const target of ['alerts', 'dlq', 'both']) {
  test('P1-3 sink timeout is bounded: ' + target, () => scenario('timeout-' + target,
    Object.fromEntries((target === 'both' ? ['alerts', 'dlq'] : [target]).map(e => [e, [{ delay_ms: 800 }]])),
    (r, s) => {
      assert.equal(r.body.alerted, target !== 'alerts' && target !== 'both');
      assert.equal(r.body.dlq, target !== 'dlq' && target !== 'both');
      assert.deepEqual(s.calls, { tickets: 0, alerts: 1, dlq: 1 });
    }));
}
test('P1-3 practice calls the selected store without app-only event_key', () => scenario('practice', {}, (r, s) => {
  assert.equal(r.body.outcome, 'success');
  assert.equal(r.history['E02 Select Store'].mode, 'practice');
  assert.equal(r.history['E02 Select Store'].alert_payload.event_key, undefined);
  assert.equal(s.calls.dlq, 1);
}, { mode: 'practice' }));
test('P1-3 app repeated parent execution uses duplicate alert ACK', () => scenario('duplicate', {}, async (r, s, { call }) => {
  const repeated = await call();
  assert.equal(repeated.body.alerted, true); assert.equal(repeated.body.dlq, true);
  assert.equal(r.history['E02 Select Store'].alert_payload.event_key, 'n8n-execution:231:unexpected-error');
  assert.equal(repeated.history['E03 Store Alert App'].body.duplicate, true);
  assert.equal(repeated.history['E03 Store Alert App'].body.count, 1);
}));
test('P1-3 trigger failure supports missing execution reference and does not invent request_id', () => scenario('trigger-failure', {}, (r, s) => {
  assert.equal(r.body.execution_ref, null); assert.equal(r.body.request_id, null);
  const payloads = r.history['E02 Select Store'];
  assert.equal(payloads.alert_payload.event_key, undefined);
  assert.equal(payloads.dlq_payload.request_id, null);
  assert.equal(payloads.dlq_payload.execution_ref, undefined);
  assert.equal(payloads.dlq_payload.safe_payload.error_kind, 'trigger_error');
  assert.equal(s.dlq_count, 1);
}, { input: { workflow: { name: 'oke-support' }, trigger: { error: { message: 'private-marker', node: { name: 'private-marker' } } } } }));
for (const input of [null, [], {}, 'private-marker']) {
  test('P1-3 malformed/missing metadata remains safe: ' + JSON.stringify(input), () => scenario('metadata', {}, r => {
    assert.equal(r.body.outcome, 'success'); assert.equal(r.body.execution_ref, null);
    assert.equal(r.body.request_id, null); assert.equal(r.body.source_workflow, 'unknown');
  }, { input }));
}
test('P1-3 raw node/workflow names and URLs are not copied as trusted metadata', () => {
  const wf = workflow();
  const input = event(); input.workflow.name = 'private-marker safe@example.invalid';
  input.execution.lastNodeExecuted = 'private-marker'; input.execution.id = 'https://bad.invalid/?token=private-marker';
  const safe = code(wf.nodes.find(n => n.name === 'E02 Safe Error Context'), input);
  assert.equal(safe.source_workflow, 'unknown'); assert.equal(safe.source_node, 'unknown');
  assert.equal(safe.execution_ref, null); assert.ok(!JSON.stringify(safe).includes('private-marker'));
});
test('P1-3 self-error name guard ends without external calls', () => scenario('self-name', {}, (r, s) => {
  assert.equal(r.body.outcome, 'skipped_self');
  assert.deepEqual(s.calls, { tickets: 0, alerts: 0, dlq: 0 });
}, { input: { workflow: { name: 'oke-errors' }, execution: { id: '999' } } }));
test('P1-3 self-error ID guard works even when renamed', () => scenario('self-id', {}, (r, s) => {
  assert.equal(r.body.outcome, 'skipped_self'); assert.equal(s.calls.alerts, 0); assert.equal(s.calls.dlq, 0);
}, { workflowId: 'local-errors-id', input: { workflow: { id: 'local-errors-id', name: 'renamed' }, execution: { id: '999' } } }));
test('P1-3 numeric parent workflow ID also prevents self re-entry', () => scenario('self-numeric-id', {}, (r, s) => {
  assert.equal(r.body.outcome, 'skipped_self'); assert.equal(s.calls.alerts, 0); assert.equal(s.calls.dlq, 0);
}, { workflowId: '42', input: { workflow: { id: 42, name: 'renamed' }, execution: { id: '999' } } }));
test('P1-3 invalid mode is a diagnostic outcome without retry/throw', () => scenario('bad-mode', {}, (r, s) => {
  assert.equal(r.body.outcome, 'configuration_error'); assert.equal(s.calls.alerts, 0); assert.equal(s.calls.dlq, 0);
}, { mode: 'invalid' }));
test('P1-3 invalid deployment URL does not leak credentials or send requests', () => scenario('bad-url', {}, (r, s) => {
  assert.equal(r.body.outcome, 'configuration_error'); assert.equal(s.calls.alerts, 0); assert.equal(s.calls.dlq, 0);
}, { url: 'http://user:private-marker@localhost:18800' }));
test('P1-3 sink authentication failure ends and never recursively rethrows', () => scenario('auth-failed', {}, (r, s) => {
  assert.equal(r.body.outcome, 'failed');
  assert.equal(r.trace.filter(n => n.startsWith('E03 Store Alert')).length, 1);
  assert.equal(r.trace.filter(n => n.startsWith('E04 Store DLQ')).length, 1);
}, { wrongKey: true }));
test('P1-3 DLQ ACK requires HTTP200 and typed positive stored/count', () => {
  const node = workflow().nodes.find(n => n.name === 'E04 Check DLQ');
  for (const reply of [{ statusCode: 201, body: { stored: 1, count: 1 } },
    { statusCode: 200, body: { stored: true, count: 1 } }, { statusCode: 200, body: { stored: 1, count: 0 } }]) {
    const result = code(node, reply, { 'E03 Check Alert': { alerted: true } });
    assert.equal(result.dlq, false);
  }
});
test('P1-3 alert ACK does not infer success from count alone or wrong types', () => {
  const node = workflow().nodes.find(n => n.name === 'E03 Check Alert');
  for (const body of [{ stored: 0, count: 1 }, { stored: true, count: 1 }, { stored: 1, count: '1' }]) {
    const result = code(node, { statusCode: 200, body }, { 'E02 Select Store': { mode: 'app', alert_payload: {} } });
    assert.equal(result.alerted, false);
  }
});
after(() => {
  if (!process.env.WONMIN_ERRORS_REPORT_BASENAME || !existsSync(file)) return;
  const name = process.env.WONMIN_ERRORS_REPORT_BASENAME;
  assert.match(name, /^[a-zA-Z0-9_-]+\.json$/);
  const hash = bytes => createHash('sha256').update(bytes).digest('hex');
  writeFileSync(new URL('runs/' + name, own), JSON.stringify({
    scope: 'P1-3 local Error Trigger payload adapter + ephemeral HTTP Mock; no automatic n8n trigger',
    created_at: new Date().toISOString(), workflow_sha256: hash(readFileSync(file)),
    mock_sha256: hash(readFileSync(new URL('tools/mock-store.py', own))),
    adapter_sha256: hash(readFileSync(new URL('./workflow-runner.mjs', import.meta.url))),
    test_sha256: hash(readFileSync(fileURLToPath(import.meta.url))), observations,
    parent_errorWorkflow_link: 'not_configured', actual_n8n: 'not_run', actual_backend_DB: 'not_run',
  }, null, 2) + '\n', { flag: 'wx' });
});
