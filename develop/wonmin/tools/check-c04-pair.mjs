// C04 boundary review: pinned peer Code -> own JSON -> HTTP Mock -> peer Code.
// The test adapter bypasses N20 Mock C04 in memory. No peer graph is changed or deployed.
import assert from 'node:assert/strict';
import { execFileSync, spawn } from 'node:child_process';
import { once } from 'node:events';
import { readFileSync, writeFileSync } from 'node:fs';
import { createInterface } from 'node:readline';
import { createHash, randomBytes } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { code, run } from '../tests/workflow-runner.mjs';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const ref = 'aac0dbf12e030ad7622fe3057654f866545c983b';
const peerFile = 'workflows/oke-support-08.json';
const readPeer = path => execFileSync('git', ['show', `${ref}:develop/dahyeok/${path}`], { cwd: root });
const peerBytes = readPeer(peerFile);
const peer = JSON.parse(peerBytes);
const ownBytes = readFileSync(new URL('../workflows/oke-handoff.json', import.meta.url));
const own = JSON.parse(ownBytes);
const mockFile = fileURLToPath(new URL('./mock-store.py', import.meta.url));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const node = name => {
  const result = peer.nodes.find(n => n.name === name);
  assert.ok(result, `Peer Code node exists: ${name}`);
  return result;
};
const key = randomBytes(24).toString('hex');
const child = spawn('python3', ['-B', mockFile, '--port', '0'], {
  env: { ...process.env, INTERNAL_API_KEY: key }, stdio: ['ignore', 'pipe', 'pipe'],
});
try {
  const lines = createInterface({ input: child.stdout });
  const firstLine = await Promise.race([
    once(lines, 'line').then(([line]) => line),
    once(child, 'exit').then(() => { throw Error('Mock exited before ready'); }),
    new Promise((_, reject) => { const timer = setTimeout(() => reject(Error('Mock startup timeout')), 5000); timer.unref(); }),
  ]);
  lines.close();
  const store = `http://127.0.0.1:${JSON.parse(firstLine).port}`;
  const env = { SERVICE_MODE: 'practice', WONMIN_PRACTICE_STORE_URL: store };
  const credentials = { WONMIN_PRACTICE_STORE_AUTH: { header: 'X-Api-Key', value: key } };
  const observations = [];
  const ops = async () => {
    const response = await fetch(store + '/_mock/ops', { headers: { 'X-Api-Key': key } });
    assert.equal(response.status, 200);
    return response.json();
  };
  function prepare(file, suffix) {
    const request = JSON.parse(readPeer('requests/' + file));
    request.request_id += '-wm-' + suffix;
    let item = { body: request };
    const history = {};
    for (const name of ['N02 Normalize input', 'N03 Validate employee MOCK', 'N04 Injection rules',
      'N06 Triage MOCK', 'N06 Parse triage', 'N07 Route triage']) {
      item = code(node(name), item, history);
      history[name] = item;
    }
    assert.deepEqual(item.codes, []);
    assert.equal(item.blocked, false);
    // C04 entry fixture: search/merge/LLM are outside this boundary review.
    if (item.decision === 'pending') item = { ...item, search: { state: 'empty' }, retrieval_reason: 'no_evidence' };
    const ready = code(node('N20 Prepare handoff'), item);
    return ready;
  }
  function consume(prepared, status, body) {
    const mapped = code(node('N20 Map handoff'), {
      ...prepared, handoff_status: status, handoff_response: body,
    });
    const finalized = code(node('N22 Finalize P0-3'), mapped);
    const filtered = code(node('N22 Output filter'), finalized);
    return { mapped: mapped.handoff, response: filtered.response, status: filtered.status_code };
  }
  async function pair(name, prepared, { transport = fetch, environment = env, expectedReason = prepared.decision_reason,
      expectedTicket = true, expectedDuplicate = false, expectedHigh = false } = {}) {
    assert.equal(prepared.handoff_needed, true);
    const before = await ops();
    const handoff = await run(own, prepared.handoff_payload, environment, credentials, transport);
    const result = consume(prepared, handoff.status, handoff.body);
    const after = await ops();
    assert.equal(result.status, 200);
    assert.equal(result.response.route, '담당자 이관');
    assert.equal(result.response.reason, expectedReason);
    if (expectedTicket) {
      assert.deepEqual(result.response.ticket, handoff.body.ticket);
      assert.equal(result.response.ticket.duplicate, expectedDuplicate);
      assert.equal(result.response.ticket.priority, expectedHigh ? 'high' : 'normal');
      assert.equal(after.tickets.filter(t => t.ticket_id === result.response.ticket.ticket_id).length, 1);
    } else {
      assert.equal(result.response.ticket, null);
      assert.equal(after.ticket_count, before.ticket_count);
    }
    observations.push({ name, kind: 'peer_code_to_own_json_to_http_mock_to_peer_code', request: prepared.handoff_payload,
      handoff_status: handoff.status, handoff_response: handoff.body, peer_mapping: result.mapped,
      support_response: result.response, ticket_count_before: before.ticket_count, ticket_count_after: after.ticket_count,
      alert_count_before: before.alert_count, alert_count_after: after.alert_count,
      ...(expectedTicket ? { same_ticket_id_observed_count: after.tickets.filter(t => t.ticket_id === result.response.ticket.ticket_id).length } : {}) });
    return result;
  }
  const normal = prepare('no-evidence.json', 'normal');
  const first = await pair('normal', normal);
  const second = await pair('duplicate', normal, { expectedDuplicate: true });
  assert.equal(first.response.ticket.ticket_id, second.response.ticket.ticket_id);
  await pair('high', prepare('urgent.json', 'urgent'), { expectedHigh: true });
  await pair('attempt3', prepare('clarify-3.json', 'attempt3'), { expectedReason: 'max_attempts' });
  const alertFailure = (url, options) => url.endsWith('/alerts')
    ? Promise.resolve(new Response(JSON.stringify({ stored: 0, count: 0 }), { status: 503 })) : fetch(url, options);
  const partial = await pair('alerts_down', prepare('no-evidence.json', 'alert-fail'),
    { transport: alertFailure, expectedReason: 'alerts_down' });
  assert.equal(partial.mapped.state, 'alerts_down');
  await pair('tickets_down_200', prepare('no-evidence.json', 'ticket-fail'), {
    transport: async () => new Response(JSON.stringify({ error: 'local_fault' }), { status: 503 }),
    expectedReason: 'tickets_down', expectedTicket: false,
  });
  await pair('configuration_503', prepare('no-evidence.json', 'config-fail'), {
    environment: { SERVICE_MODE: 'invalid' }, expectedReason: 'tickets_down', expectedTicket: false,
  });
  const concurrent = prepare('no-evidence.json', 'parallel');
  const beforeParallel = await ops();
  const responses = await Promise.all(Array.from({ length: 4 }, () => run(own, concurrent.handoff_payload, env, credentials)));
  const mapped = responses.map(r => consume(concurrent, r.status, r.body));
  const afterParallel = await ops();
  assert.equal(new Set(mapped.map(r => r.response.ticket.ticket_id)).size, 1);
  assert.equal(mapped.filter(r => r.response.ticket.duplicate).length, 3);
  assert.equal(afterParallel.ticket_count - beforeParallel.ticket_count, 1);
  observations.push({ name: 'parallel4', kind: 'paired_local_concurrent', responses: mapped.map(r => r.response),
    ticket_count_before: beforeParallel.ticket_count, ticket_count_after: afterParallel.ticket_count });

  const prepared = prepare('no-evidence.json', 'schema');
  const good = { ok: true, ticket: { ticket_id: 'T-9001', priority: 'normal', duplicate: false }, reason: null, alerted: true, dlq: false };
  for (const [name, status, raw] of [
    ['invalid_duplicate_type', 200, { ...good, ticket: { ...good.ticket, duplicate: 'false' } }],
    ['invalid_priority', 200, { ...good, ticket: { ...good.ticket, priority: 'high' } }],
    ['transport_timeout', 0, null],
    ['http_401', 401, good],
    ['http_403', 403, good],
  ]) {
    const result = consume(prepared, status, raw);
    assert.equal(result.response.ticket, null);
    assert.equal(result.response.reason, 'handoff_unavailable');
    observations.push({ name, kind: 'synthetic_peer_mapper_boundary_probe', support_response: result.response });
  }
  const fixture = JSON.parse(readPeer('fixtures/c04-wonmin-samples.json'));
  for (const [name, expectedState] of [['normal', 'created'], ['duplicate', 'created'],
    ['alerts_down', 'alerts_down'], ['tickets_down', 'tickets_down']]) {
    const probe = fixture.results[name];
    const result = consume(prepared, probe.status, probe.body);
    assert.equal(result.mapped.state, expectedState);
    observations.push({ name: 'peer_fixture_' + name, kind: 'peer_synthetic_fixture', peer_mapping: result.mapped });
  }
  const http = peer.nodes.filter(n => n.type.endsWith('.httpRequest'));
  assert.equal(http.length, 0);
  assert.equal(peer.connections['N20 Handoff gate'].main[0][0].node, 'N20 Mock C04');
  const report = { created_at: new Date().toISOString(), dahyeok_commit: ref,
    reviewed_development_file: 'develop/dahyeok/' + peerFile,
    source_sha256: { [peerFile]: hash(peerBytes), 'own_oke_handoff': hash(ownBytes),
      'own_mock_store': hash(readFileSync(mockFile)), 'review_script': hash(readFileSync(fileURLToPath(import.meta.url))) },
    scope: 'Local C04 Code boundary + own JSON adapter + real ephemeral C05 HTTP Mock. Test adapter supplies the peer Mock boundary result; source graphs unchanged.',
    observations, checks_passed: observations.length,
    result: { request_generation: 'compatible', response_mapping: 'compatible_with_current_own_P1-1',
      alerts_down_ok_false_ticket_preserved: true, peer_graph_still_uses: 'N20 Mock C04',
      peer_http_request_node_count: http.length, actual_C04_HTTP_auth_timeout: 'not_implemented_in_peer_graph',
      n8n_execution: 'not_run', real_backend_DB: 'not_run', retry_DLQ_errors: 'outside_P1-1_scope' } };
  if (process.argv.length === 4 && process.argv[2] === '--output') {
    const filename = process.argv[3];
    assert.match(filename, /^[a-zA-Z0-9_-]+\.json$/);
    writeFileSync(new URL('../runs/' + filename, import.meta.url), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
    console.log(`Report: develop/wonmin/runs/${filename}`);
  } else {
    assert.equal(process.argv.length, 2, 'Use --output NEW_BASENAME.json or no arguments');
    console.log(JSON.stringify(report, null, 2));
  }
  console.error(`Local C04 observations: ${observations.length}/${observations.length}; source C04 HTTP remains Mock; n8n not run`);
} finally {
  if (child.exitCode === null) { child.kill(); await once(child, 'exit'); }
}
