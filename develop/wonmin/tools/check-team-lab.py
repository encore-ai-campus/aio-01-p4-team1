#!/usr/bin/env python3
"""Probe published lab routes without private values or raw n8n execution exports."""
import datetime
import importlib.util
import json
from pathlib import Path

OWN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lab', OWN / 'tools/linux-lab.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def main():
    assert 'ubuntu' in Path('/etc/os-release').read_text().lower()
    values = dict(x.split('=', 1) for x in lab.ENVFILE.read_text().splitlines() if '=' in x)
    key = {'X-Team-Key': values['N8N_WEBHOOK_KEY']}
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    report = {'scope': 'actual private Ubuntu n8n HTTP; Mock ticket sink and unavailable peer dependencies explicit',
              'stamp': stamp}
    report['container_state'] = json.loads(lab.command(['docker', 'inspect', '--format', '{{json .State.Running}}',
        'wonmin-p13-lab-n8n-1']))
    assert report['container_state'] is True
    report['rag_image_command'] = json.loads(lab.command(['docker', 'image', 'inspect', 'wonmin-rag-lab:95ef45f', '--format', '{{json .Config.Cmd}}']))
    assert report['rag_image_command'] == ['python', 'tools/search_http.py', '--host', '0.0.0.0', '--port', '8765']
    report['rag_network_without_key'] = json.loads(lab.compose('exec', '-T', 'n8n', 'node', '-e',
        'fetch("http://rag-search:8765/webhook/oke-search",{method:"POST",body:"{}"}).then(async r=>console.log(JSON.stringify({status:r.status,body:await r.json()})))'))
    assert report['rag_network_without_key']['status'] == 401
    ids = json.loads((OWN / '.runtime/workflow-ids.json').read_text())
    report['workflows'] = lab.metadata('workflows', ids)
    for name in ('support', 'search', 'handoff', 'errors'):
        item = next(w for w in report['workflows'] if w['id'] == ids[name])
        assert item['active']
        if name != 'errors':
            assert json.loads(item['settings'])['errorWorkflow'] == ids['errors']
    script = r'''
const {DatabaseSync}=require('node:sqlite');
const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});
const r=d.prepare("SELECT e.id,e.status,e.mode,x.data FROM execution_entity e JOIN execution_data x ON x.executionId=e.id WHERE e.workflowId=? AND e.status='success' AND e.mode='manual' ORDER BY e.id DESC LIMIT 1").get(process.argv[1]);
let result=null;
if(r){const p=require('/usr/local/lib/node_modules/n8n/node_modules/flatted').parse;const j=p(r.data);
 const output=j.resultData?.runData?.['안전한 검증 결과']?.[0]?.data?.main?.[0]?.[0]?.json;
 result={id:r.id,status:r.status,mode:r.mode,mock:output?.mode==='mock',ok:output?.ok===true,first:output?.first,second:output?.second};}
console.log(JSON.stringify(result));
'''
    report['index_manual_execution'] = json.loads(lab.compose('exec', '-T', 'n8n', 'node', '-e', script, ids['index']))
    for name in ('support', 'search', 'handoff'):
        report[name + '_without_key'] = lab.request(15678, '/webhook/oke-' + name, {})['status']
        assert report[name + '_without_key'] in (401, 403)
    search = {'request_id': 'wm-redeploy-search', 'query': 'VPN 연결 안내', 'type': 'network', 'access_levels': ['all'], 'top_k': 3}
    report['search_valid_missing_embedding'] = lab.request(15678, '/webhook/oke-search', search, key)
    assert report['search_valid_missing_embedding'] == {'status': 503, 'body': {'ok': False, 'evidence': [], 'reason': 'search_unavailable'}}
    report['search_unverified_it_rejected'] = lab.request(15678, '/webhook/oke-search', {**search, 'access_levels': ['all', 'it']}, key)
    assert report['search_unverified_it_rejected']['status'] == 400
    report['support_invalid'] = lab.request(15678, '/webhook/oke-support', {}, key)
    assert report['support_invalid']['status'] == 400
    report['support_missing_employee_api'] = lab.request(15678, '/webhook/oke-support', {
        'request_id': 'wm-redeploy-support', 'user': '박서연', 'question': 'VPN이 계속 끊겨요', 'attempt': 1}, key, timeout=45)
    ticket = {'request_id': 'wm-redeploy-ticket-' + stamp, 'requester': '박서연', 'title': 'VPN 합성 시험',
              'category': 'network', 'priority': 'normal', 'reason': 'no_evidence'}
    report['handoff_new_mock'] = lab.request(15678, '/webhook/oke-handoff', ticket, key)
    report['handoff_duplicate_mock'] = lab.request(15678, '/webhook/oke-handoff', ticket, key)
    a, b = report['handoff_new_mock'], report['handoff_duplicate_mock']
    assert a['status'] == b['status'] == 200 and a['body']['ok'] and b['body']['ok']
    assert a['body']['ticket']['duplicate'] is False and b['body']['ticket']['duplicate'] is True
    assert a['body']['ticket']['ticket_id'] == b['body']['ticket']['ticket_id']
    report['local_ollama'] = lab.request(15678, '/webhook/wonmin-local-llm', {}, timeout=150)
    assert report['local_ollama']['status'] == 200 and report['local_ollama']['body']['ok']
    report['backend_live'] = lab.request(18000, '/health/live')
    report['backend_save_unimplemented'] = lab.request(18000, '/tickets', {
        'key': 'wm-redeploy-app', 'requester': '박서연', 'title': '합성', 'category': 'network', 'priority': 'normal'},
        {'X-Api-Key': values['INTERNAL_API_KEY']})
    assert report['backend_save_unimplemented']['status'] == 501
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    assert not any(v in text for v in values.values() if len(v) >= 16)
    name = 'team-http-check-' + stamp + '.json'
    with (OWN / 'runs' / name).open('x') as output:
        output.write(text)
    print(json.dumps({'report': name, 'support': report['support_missing_employee_api'],
                      'search': report['search_valid_missing_embedding']['status'], 'handoff_new_duplicate': 'passed',
                      'local_llm': report['local_ollama']['status']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
