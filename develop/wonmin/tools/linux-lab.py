#!/usr/bin/env python3
"""Operate only the isolated wonmin-p13-lab stack, from inside Ubuntu."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

OWN = Path(__file__).resolve().parents[1]
ENVFILE = OWN / '.runtime/lab.env'
COMPOSE = ['docker', 'compose', '--env-file', str(ENVFILE), '-f', str(OWN / 'deploy/compose.lab.yaml')]


def command(args, timeout=90):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if r.returncode:
        # Commands receive secret values only via files/env, never printed as arguments.
        raise RuntimeError('command failed: ' + str(r.returncode) + ': ' + r.stderr[-300:])
    return r.stdout


def compose(*args, timeout=90):
    return command(COMPOSE + list(args), timeout=timeout)


def metadata(kind, ids):
    script = r'''
const {DatabaseSync}=require('node:sqlite');
const db=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});
const ids=JSON.parse(process.argv[1]),kind=process.argv[2];
const marks=Object.values(ids).map(()=>'?').join(',');
if(kind==='workflows') console.log(JSON.stringify(db.prepare(`SELECT id,name,active,settings,activeVersionId FROM workflow_entity WHERE id IN (${marks})`).all(...Object.values(ids))));
else {
 const rows=db.prepare(`SELECT e.id,e.workflowId,e.status,e.mode,e.startedAt,e.stoppedAt,d.data FROM execution_entity e LEFT JOIN execution_data d ON d.executionId=e.id WHERE e.workflowId IN (${marks}) ORDER BY e.id`).all(...Object.values(ids));
 let parse;try{parse=require('/usr/local/lib/node_modules/n8n/node_modules/flatted').parse}catch{}
 console.log(JSON.stringify(rows.map(r=>{
   let data={};try{data=parse?parse(r.data):JSON.parse(r.data)}catch{}
   const outcome=data?.resultData?.runData?.['E05 Outcome']?.[0]?.data?.main?.[0]?.[0]?.json??null;
   return {id:r.id,workflow_id:r.workflowId,status:r.status,mode:r.mode,started_at:r.startedAt,stopped_at:r.stoppedAt,
     last_node:data?.resultData?.lastNodeExecuted??null,outcome};
 })));
}
'''
    return json.loads(compose('exec', '-T', 'n8n', 'node', '-e', script, json.dumps(ids), kind))


def request(port, path, body=None, headers=None, timeout=10):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=data,
                                 headers={'Content-Type': 'application/json', **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
            return {'status': response.status, 'body': json.loads(raw) if raw else None}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            value = json.loads(raw)
        except ValueError:
            value = {'non_json_error': True}
        return {'status': e.code, 'body': value}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New basename under own runs')
    args = parser.parse_args()
    if Path(args.output).name != args.output or not args.output.endswith('.json'):
        parser.error('output must be a new JSON basename')
    assert 'ubuntu' in Path('/etc/os-release').read_text().lower(), 'Execute inside Ubuntu'
    values = dict(line.split('=', 1) for line in ENVFILE.read_text().splitlines() if '=' in line)
    ids = json.loads((OWN / '.runtime/workflow-ids.json').read_text())
    report = {'scope': 'actual Ubuntu Docker Compose / actual n8n / separate peer backend and PG',
              'os': Path('/etc/os-release').read_text().splitlines()[0], 'workflow_ids': ids}
    print(json.dumps({'stage': 'publish_selected_lab_parents'}), flush=True)
    existing = metadata('workflows', ids)
    published = {w['id'] for w in existing if w['active']}
    changed = False
    for name in ('errors', 'handoff', 'failure', 'llm'):
        if ids[name] not in published:
            compose('exec', '-T', 'n8n', 'n8n', 'publish:workflow', '--id=' + ids[name])
            changed = True
    if changed:
        compose('restart', 'n8n')
        for _ in range(30):
            try:
                if request(15678, '/healthz')['status'] == 200:
                    break
            except (OSError, urllib.error.URLError):
                pass
            time.sleep(1)
    report['workflows'] = metadata('workflows', ids)
    errors_id = ids['errors']
    parent = next(w for w in report['workflows'] if w['id'] == ids['failure'])
    assert json.loads(parent['settings'])['errorWorkflow'] == errors_id
    report['actual_error_workflow_link_verified'] = True
    print(json.dumps({'stage': 'parent_error_workflow_id_verified'}), flush=True)
    payload = {'request_id': 'wm-ubuntu-normal-' + str(int(time.time())), 'requester': '박서연',
               'title': 'VPN 점검', 'category': 'network', 'priority': 'normal', 'reason': 'no_evidence'}
    headers = {'X-Team-Key': values['N8N_WEBHOOK_KEY']}
    # Publication service polls; retry only 404 before any workflow runs.
    for _ in range(30):
        ready = request(15678, '/webhook/oke-handoff', payload, headers)
        if ready['status'] != 404:
            break
        time.sleep(1)
    report['handoff_normal'] = ready
    baseline = max((int(e['id']) for e in metadata('executions', ids)), default=0)
    report['controlled_error_http'] = request(15678, '/webhook/wonmin-p13-failure', {**payload, 'request_id': 'wm-ubuntu-controlled-error'})
    print(json.dumps({'stage': 'automatic_parent_error_requested', 'status': report['controlled_error_http']['status']}), flush=True)
    for _ in range(30):
        executions = metadata('executions', ids)
        errors = [e for e in executions if e['workflow_id'] == errors_id and int(e['id']) > baseline and e['status'] not in ('new', 'running')]
        if errors:
            break
        time.sleep(1)
    report['executions'] = executions
    report['mock_observed'] = request(18800, '/_mock/ops', headers={'X-Api-Key': values['INTERNAL_API_KEY']})
    report['backend_live'] = request(18000, '/health/live')
    report['backend_ready'] = request(18000, '/health/ready')
    report['backend_tickets'] = request(18000, '/tickets', {'key': payload['request_id'], 'title': '합성 문의',
      'requester': '박서연', 'category': 'network', 'priority': 'normal'}, {'X-Api-Key': values['INTERNAL_API_KEY']})
    report['backend_alerts'] = request(18000, '/alerts', {'workflow': 'oke-errors', 'node': 'lab',
      'message': '비민감 시험', 'severity': 'high'}, {'X-Api-Key': values['INTERNAL_API_KEY']})
    report['backend_dlq'] = request(18000, '/dlq', {'request_id': None, 'workflow': 'oke-errors', 'node': 'lab',
      'reason': 'unexpected', 'safe_payload': {'stage': 'unexpected'}}, {'X-Api-Key': values['INTERNAL_API_KEY']})
    print(json.dumps({'stage': 'actual_backend_probed', 'ticket_status': report['backend_tickets']['status']}), flush=True)
    report['local_llm'] = request(15678, '/webhook/wonmin-local-llm', {'probe': 'local_llm'}, timeout=150)
    report['docker_version'] = command(['docker', 'version', '--format', '{{.Server.Version}}']).strip()
    report['compose_version'] = command(['docker', 'compose', 'version', '--short']).strip()
    report['n8n_version'] = compose('exec', '-T', 'n8n', 'n8n', '--version').strip()
    # Guard all secret values before writing any execution summary.
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    for secret in values.values():
        if len(secret) >= 16:
            assert secret not in text, 'Refuse to save a secret in report'
    with (OWN / 'runs' / args.output).open('x') as target:
        target.write(text)
    print(json.dumps({'report': args.output, 'automatic_error_executions': len(errors),
      'normal_status': ready['status'], 'local_llm_status': report['local_llm']['status']}), flush=True)


if __name__ == '__main__':
    main()
