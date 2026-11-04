// Read-only review of a pinned peer workflow. Does not publish/import/call n8n.
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { run, code } from '../tests/workflow-runner.mjs';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const ref = '9bda7639aaeee3f6dca59f6aabd91e61fa05a847';
const source = path => execFileSync('git', ['show', `${ref}:develop/dahyeok/${path}`], { cwd: root });
const parse = path => JSON.parse(source(path));
const hash = data => createHash('sha256').update(data).digest('hex');
const peerPath = 'workflows/oke-support-02.json';
const peer = parse(peerPath);
const ownFile = new URL('../workflows/oke-handoff.json', import.meta.url);
const own = JSON.parse(readFileSync(ownFile));
const doc = source('Doc/SPEC.md').toString('utf8');
const section = doc.split('### C04 handoff')[1]?.split('## 7.')[0];
assert.ok(section, 'C04 documentation section exists at pinned ref');
const match = section.match(/```json\s*([\s\S]*?)```/);
assert.ok(match, 'Documented C04 request example exists');
const sample = JSON.parse(match[1]);
const validation = code(own.nodes.find(n => n.name === 'H02 Validate and Map'), { body: sample });
assert.equal(validation.valid, true);
assert.equal(validation.ticket_payload.key, 'dh-urgent-001');
assert.equal(validation.ticket_payload.requester, '박서연');
assert.equal(validation.ticket_payload.priority, 'high');
const httpNodes = peer.nodes.filter(n => n.type.endsWith('.httpRequest'));
assert.equal(httpNodes.length, 0, 'Latest P0-2 has no outgoing HTTP implementation');
const scenarios = [
  { name: 'attempt-1', path: 'requests/clarify-1.json', route: '보완 질문' },
  { name: 'attempt-2', path: 'requests/clarify-2.json', route: '보완 질문' },
  { name: 'attempt-3', path: 'requests/clarify-3.json', route: '담당자 이관', decision: 'handoff_mock' },
  { name: 'context-resolved', path: 'requests/clarify-context.json', route: '담당자 이관', decision: 'pending' },
  { name: 'urgent', body: { request_id: 'wm-c04-urgent-review', user: '박서연',
      question: '피싱 메일 링크를 눌렀어요. 제 VPN 인증서 건 T-1002 상태도 알려주세요.', attempt: 1 },
    route: '담당자 이관', decision: 'handoff_mock', priority: 'high' },
  { name: 'injection', path: 'requests/injection.json', route: '차단' },
];
const observations = [];
for (const scenario of scenarios) {
  let calls = 0;
  const input = scenario.body ?? parse(scenario.path);
  const result = await run(peer, input, {}, {}, async () => {
    calls += 1;
    throw Error('No peer C04 HTTP call is expected in P0-2');
  });
  assert.equal(result.status, 200);
  assert.equal(result.body.route, scenario.route);
  assert.equal(result.body.ticket, null);
  const intermediate = result.history['N07 Route triage'];
  if (scenario.decision) assert.equal(intermediate.decision, scenario.decision);
  if (scenario.priority) assert.equal(intermediate.priority, scenario.priority);
  if (scenario.route === '담당자 이관') assert.equal(result.body.reason, 'not_implemented');
  assert.equal(calls, 0);
  observations.push({ scenario: scenario.name, input_source: scenario.path ?? 'own synthetic urgent probe',
    response: result.body, ...(intermediate ? { decision: intermediate.decision,
      decision_reason: intermediate.decision_reason ?? null, priority: intermediate.priority ?? null } : {}),
    outgoing_http_calls: calls, trace: result.trace });
}
const report = {
  scope: 'Pinned peer JSON Code/expression local adapter; not n8n or live C04',
  dahyeok_commit: ref,
  reviewed_development_file: `develop/dahyeok/${peerPath}`,
  source_sha256: { [peerPath]: hash(source(peerPath)), 'Doc/SPEC.md': hash(source('Doc/SPEC.md')) },
  own_workflow_sha256: hash(readFileSync(ownFile)),
  documented_c04_sample: { body: sample, producer_status: 'SPEC example only; N20 not implemented',
    own_validator: 'accepted', c05_projection: validation.ticket_payload },
  observations,
  conclusion: { local_probes: '6/6 expected P0-2 observations',
    outgoing_http_node_count: httpNodes.length, c04_http_call: 'not_implemented',
    c04_header_auth_at_caller: 'not_implemented', c04_timeout_at_caller: 'not_implemented',
    c04_response_mapping_at_caller: 'not_implemented', real_n8n_connection: 'not_run' },
};
if (process.argv.length === 4 && process.argv[2] === '--output') {
  const filename = process.argv[3];
  assert.match(filename, /^[a-zA-Z0-9_-]+\.json$/);
  writeFileSync(new URL('../runs/' + filename, import.meta.url), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
  console.log(`Report: develop/wonmin/runs/${filename}`);
} else {
  assert.equal(process.argv.length, 2, 'Use --output NEW_BASENAME.json or no arguments');
  console.log(JSON.stringify(report, null, 2));
}
console.error('C04 document request: accepted; peer P0-2 local probes: 6/6; live connection: not implemented/not run');
