#!/usr/bin/env python3
"""Run P1-5 HTTP adapter Code with synthetic replies; never sends HTTP."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = r"""
const fs = require('fs'), vm = require('vm'), assert = require('assert/strict');
const flow = JSON.parse(fs.readFileSync(0, 'utf8'));
const nodes = Object.fromEntries(flow.nodes.map(node => [node.name, node]));
let count = 0;
const env = {SERVICE_MODE:'practice', DATA_API_URL:'http://data-api:8800'};
const run = (name, input, previous = {}, overrideEnv = env) => {
  const items = vm.runInNewContext('(function(){' + nodes[name].parameters.jsCode + '})()', {
    $input: {first: () => ({json: input})},
    $: nodeName => ({first: () => ({json: previous[nodeName]})}),
    $env: overrideEnv,
  }, {timeout: 1000});
  assert.equal(items.length, 1, name + ' must return one item');
  return items[0].json;
};
const check = (name, fn) => {fn(); count++; process.stdout.write('PASS ' + name + ' (synthetic adapter)\n');};
const body = {request_id:'adapter-probe',user:'박서연',question:'T-1002 처리 상태를 알려주세요',attempt:1};
const base = run('N02 Normalize input', {body});
check('real mode from SERVICE_MODE', () => {
  assert.equal(base.integration_mode, 'real'); assert.equal(base.triage_mode, 'agent');
  assert.equal(run('N02 Normalize input',{body},{},{SERVICE_MODE:'other'}).integration_mode,'unavailable');
});
const people = {items:[{name:'박서연',dept:'재무팀'},{name:'김민지',dept:'IT팀'}]};
const employee = run('N03 Capture employee',{statusCode:200,body:people},{'N02 Normalize input':base});
check('employee verified department', () => {
  assert.equal(employee.employee_lookup,'ok'); assert.equal(employee.dept,'재무팀');
  assert.deepEqual(Array.from(employee.access_levels),['all']);
});
check('employee unknown versus outage', () => {
  const prior={'N02 Normalize input':base};
  assert.deepEqual(Array.from(run('N03 Capture employee',{statusCode:200,body:{items:[]}},prior).codes),['unknown_user']);
  assert.equal(run('N03 Capture employee',{statusCode:503,body:{error:'down'}},prior).employee_lookup,'unavailable');
  assert.equal(run('N03 Validate employee MOCK',base).employee_lookup,'unavailable');
});
check('employee department cannot be elevated', () => {
  const prior={'N02 Normalize input':base};
  const changed=run('N03 Capture employee',{statusCode:200,body:{items:[{name:'박서연',dept:'IT팀'}]}},prior);
  assert.equal(changed.employee_lookup,'unavailable');
  assert.ok(!changed.access_levels);
  const outsider=run('N02 Normalize input',{body:{...body,user:'외부직원'}});
  const extra=run('N03 Capture employee',{statusCode:200,body:{items:[{name:'외부직원',dept:'IT팀'}]}},
    {'N02 Normalize input':outsider});
  assert.deepEqual(Array.from(extra.codes),['unknown_user']);
});
const prepared = {...employee,decision:'pending',triage:{type:'network',urgency:'normal',ticket_id:'T-1002',needs_action:false,missing:[]}};
const searchBase = run('N08 Build search input',prepared);
check('C03 request identity and access', () => {
  assert.equal(searchBase.search_request.top_k,3);
  assert.deepEqual(Array.from(searchBase.search_request.access_levels),['all']);
  assert.equal(searchBase.search_request.request_id,body.request_id);
});
const capturedSearch = reply => run('N09 Capture C03',reply,{'N08 Build search input':searchBase});
check('C03 empty versus unavailable', () => {
  const empty=run('N09 Normalize search',capturedSearch({statusCode:200,body:{ok:true,evidence:[],reason:'no_evidence'}}));
  const down=run('N09 Normalize search',capturedSearch({statusCode:503,body:{ok:false,evidence:[],reason:'search_unavailable'}}));
  assert.equal(empty.search.state,'empty'); assert.equal(down.search.state,'unavailable');
  assert.equal(run('N09 Normalize search',capturedSearch({error:'timeout'})).search.state,'invalid');
});
const ticketBase = run('N10 Build ticket lookup',searchBase);
check('ticket GET uses verified requester', () => {
  assert.equal(ticketBase.lookup_request.requester,'박서연');
  assert.equal(ticketBase.lookup_request.ticket_id,'T-1002');
  assert.ok(ticketBase.lookup_request.url.includes(encodeURIComponent('박서연')));
});
const capturedTicket = reply => run('N10 Capture ticket',reply,{'N10 Build ticket lookup':ticketBase});
check('ticket 403, 404 and timeout', () => {
  assert.equal(run('N10 Normalize ticket',capturedTicket({statusCode:403,body:{contact:'secret'}})).ticket_lookup.state,'forbidden');
  assert.equal(run('N10 Normalize ticket',capturedTicket({statusCode:404,body:{error:'missing'}})).ticket_lookup.state,'not_found');
  assert.equal(run('N10 Normalize ticket',capturedTicket({error:'timeout'})).ticket_lookup.state,'unavailable');
});
check('ticket body masked before writer', () => {
  const result=run('N10 Normalize ticket',capturedTicket({statusCode:200,body:{ticket_id:'T-1002',status:'처리 중',note:'02-0000-0000',contact:{phone:'TEST_PHONE'}}}));
  assert.equal(result.ticket_lookup.state,'ok'); assert.equal(result.ticket_lookup.data.note,'***');
  assert.equal(result.mask_count,2); assert.ok(!('contact' in result.ticket_lookup.data));
});
const handoffBase = run('N20 Prepare handoff',{...searchBase,search:{state:'empty',evidence:[]},decision_reason:'no_evidence'});
const capturedHandoff = reply => run('N20 Capture C04',reply,{'N20 Prepare handoff':handoffBase});
check('C04 request and successful mapping', () => {
  assert.equal(handoffBase.handoff_payload.requester,'박서연');
  assert.equal(handoffBase.handoff_payload.priority,'normal');
  const result=run('N20 Map handoff',capturedHandoff({statusCode:200,body:{ok:true,ticket:{ticket_id:'T-2101',priority:'normal',duplicate:false},reason:null,alerted:true,dlq:false}}));
  assert.equal(result.handoff.state,'created'); assert.equal(result.handoff.ticket.ticket_id,'T-2101');
  assert.equal(result.handoff_mock,false);
});
check('C04 alerts and transport failure remain distinct', () => {
  const alert=run('N20 Map handoff',capturedHandoff({statusCode:200,body:{ok:false,ticket:{ticket_id:'T-2101',priority:'normal',duplicate:false},reason:'alerts_down',alerted:false,dlq:false}}));
  const down=run('N20 Map handoff',capturedHandoff({statusCode:200,body:{ok:false,ticket:null,reason:'tickets_down',alerted:true,dlq:true}}));
  const unknown=run('N20 Map handoff',capturedHandoff({error:'timeout'}));
  assert.equal(alert.handoff.state,'alerts_down'); assert.equal(down.handoff.state,'tickets_down');
  assert.equal(unknown.handoff.state,'unavailable');
});
check('real agent modes avoid synthetic answer branch', () => {
  const writer=run('N13 Prepare writer',{...searchBase,usable_evidence:[{doc:'remote-work-vpn',section:'접속',text:'합성',score:0.8}],ticket_lookup:{state:'skipped',data:null}});
  assert.equal(writer.writer_mode,'agent');
  const verifier=run('N14 Prepare verifier',{...writer,draft:{answer:'합성',used_sources:[],used_ticket:false}});
  assert.equal(verifier.verifier_mode,'agent');
});
process.stdout.write('local HTTP adapter result: '+count+'/'+count+'; no HTTP/n8n calls\n');
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow", nargs="?", default="workflows/oke-support-12.json")
    parser.add_argument("--node-container")
    args = parser.parse_args()
    flow = json.loads((ROOT / args.workflow).read_text(encoding="utf-8"))
    if args.node_container:
        cmd = ["docker", "exec", "-i", args.node_container, "node", "-e", RUNNER]
    elif shutil.which("node"):
        cmd = ["node", "-e", RUNNER]
    else:
        print("ERROR: Node.js unavailable; supply --node-container", file=sys.stderr)
        return 1
    result = subprocess.run(cmd, input=json.dumps(flow, ensure_ascii=False), text=True,
                            capture_output=True, check=False)
    print(result.stdout, end="")
    if result.returncode:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
