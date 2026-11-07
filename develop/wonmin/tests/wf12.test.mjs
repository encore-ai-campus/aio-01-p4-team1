import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = new URL('../../../', import.meta.url);
// Exercise the configured deployment source: reverting its pin must break the WF-12 behavior tests.
const pin = execFileSync('python3', ['-B', '-c',
  'import importlib.util,sys;s=importlib.util.spec_from_file_location("prepare",sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(m.SOURCES["dahyeok"])',
  fileURLToPath(new URL('develop/wonmin/tools/prepare-team-deploy.py', root)),
], { encoding: 'utf8' }).trim();
const workflow = JSON.parse(execFileSync('git', ['show', `${pin}:develop/dahyeok/workflows/oke-support-13.json`],
  { cwd: fileURLToPath(root), encoding: 'utf8' }));
const finalizeCode = workflow.nodes.find(n => n.name === 'N22 Finalize P0-3').parameters.jsCode;
const base = {
  request_id: 'wf12-local-contract', codes: [], employee_lookup: 'ok', user: '박서연', dept: '재무팀',
  urgent_pre_handoff: true, handoff_done: true, triage_executed: true,
  triage: { type: 'security' }, decision: 'handoff_mock', handoff_mock: false,
  handoff: { state: 'created', ticket: { ticket_id: 'T-2999', priority: 'high', duplicate: false } },
  ticket_lookup: { state: 'ok', data: { ticket_id: 'T-1002', title: 'VPN 인증서 재발급', status: '처리 중' } },
};
function finalize(extra = {}) {
  const input = structuredClone({ ...base, ...extra });
  return JSON.parse(JSON.stringify(vm.runInNewContext(`(function(){${finalizeCode}})()`, {
    $input: { first: () => ({ json: input }) },
  }, { timeout: 1000 })[0].json));
}
function checkCase(c, result) {
  assert.equal(result.status_code, c.expect.http_status);
  for (const [path, want] of Object.entries(c.expect.equals ?? {})) {
    assert.deepEqual(path.split('.').reduce((value, key) => value?.[key], result.response), want, path);
  }
  for (const doc of c.expect.source_docs_include ?? []) {
    assert.ok(result.response.sources.some(source => source.doc === doc), `required source ${doc}`);
  }
}
for (const file of ['cases/team.json', 'develop/wonmin/cases/team.json']) {
  const c = JSON.parse(readFileSync(new URL(file, root))).cases.find(c => c.id === 'TM-05');
  test(`${file} TM-05 accepts the public WF-12 response with no policy evidence`, () => {
    const result = finalize();
    assert.equal(result.response.route, '담당자 이관');
    assert.equal(result.response.ticket.priority, 'high');
    assert.deepEqual(result.response.sources, []);
    for (const part of ['긴급', 'T-2999', '사내망', 'T-1002', '처리 중']) assert.ok(result.response.answer.includes(part), part);
    assert.match(result.response.answer, /사내망[^.]*?(끊|분리)/);
    checkCase(c, result);
  });
  test(`${file} TM-05 rejects a security-incident source leak to the public employee`, () => {
    const leaked = finalize();
    leaked.response.sources = [{ doc: 'security-incident', section: 'IT 전용', score: 1 }];
    assert.throws(() => checkCase(c, leaked));
  });
}
test('WF-12 never appends a forbidden ticket status, even if stale data is present', () => {
  const result = finalize({ ticket_lookup: { state: 'forbidden', data: base.ticket_lookup.data } });
  assert.ok(!result.response.answer.includes('T-1002'));
  assert.ok(result.response.answer.includes('사내망'));
  assert.deepEqual(result.response.sources, []);
});
test('WF-12 keeps the verified ticket and explains alerts_down', () => {
  const result = finalize({ handoff: { ...base.handoff, state: 'alerts_down' } });
  assert.equal(result.response.ticket.ticket_id, 'T-2999');
  assert.equal(result.response.reason, 'alerts_down');
  assert.ok(result.response.answer.includes('알림 전송에 실패'));
  assert.ok(result.response.answer.includes('사내망'));
});
test('WF-12 tickets_down retains the first step without claiming definite save failure', () => {
  const result = finalize({ handoff: { state: 'tickets_down', ticket: null } });
  assert.equal(result.response.ticket, null);
  assert.equal(result.response.reason, 'tickets_down');
  assert.ok(result.response.answer.includes('확인하지 못했습니다'));
  assert.ok(result.response.answer.includes('같은 요청 ID'));
  assert.ok(result.response.answer.includes('사내망'));
  assert.ok(!result.response.answer.includes('접수하지 못했습니다'));
});
test('B wording applies to non-security tickets_down without adding a security first step', () => {
  const result = finalize({ urgent_pre_handoff: false, triage: { type: 'network' }, handoff: { state: 'tickets_down', ticket: null } });
  assert.equal(result.response.reason, 'tickets_down');
  assert.ok(result.response.answer.includes('확인하지 못했습니다'));
  assert.ok(result.response.answer.includes('같은 요청 ID'));
  assert.ok(!result.response.answer.includes('접수하지 못했습니다'));
  assert.ok(!result.response.answer.includes('사내망'));
});
