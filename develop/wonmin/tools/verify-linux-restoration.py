#!/usr/bin/env python3
"""Verify the restored lab after the error matrix; never publish the failure parent."""
import importlib.util
import json
from pathlib import Path
import subprocess
import time

OWN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('matrix', OWN / 'tools/linux-errors-matrix.py')
matrix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(matrix)
lab = matrix.lab


def main():
    assert 'ubuntu' in Path('/etc/os-release').read_text().lower()
    values = dict(line.split('=', 1) for line in lab.ENVFILE.read_text().splitlines() if '=' in line)
    ids = json.loads((OWN / '.runtime/workflow-ids.json').read_text())
    restored = json.loads((OWN / '.runtime/n8n-import/restored-parent.json').read_text())[0]
    hook = next(n for n in restored['nodes'] if n['name'] == 'H01 Handoff Webhook')
    assert hook['parameters']['authentication'] == 'headerAuth'
    assert 'throw new Error' not in next(n for n in restored['nodes'] if n['name'] == 'H03 Select Store')['parameters']['jsCode']
    report = {'scope': 'actual Ubuntu restoration and local-model/peer-backend/PostgreSQL checks',
              'workflow_ids': ids, 'restored_authenticated_parent_source': True}
    # Remove the deliberate-error copy from the import bundle as well as the running service.
    bundle = OWN / '.runtime/n8n-import/workflows.json'
    workflows = json.loads(bundle.read_text())
    workflows = [restored if w['id'] == ids['failure'] else w for w in workflows]
    bundle.write_text(json.dumps(workflows, ensure_ascii=False))
    lab.compose('exec', '-T', 'n8n', 'n8n', 'unpublish:workflow', '--id=' + ids['failure'])
    lab.compose('restart', 'n8n')
    matrix.wait_ready(15678, '/healthz')
    time.sleep(2)
    report['workflows'] = lab.metadata('workflows', ids)
    assert not next(w for w in report['workflows'] if w['id'] == ids['failure'])['active']
    parent = next(w for w in report['workflows'] if w['id'] == ids['handoff'])
    assert parent['active'] and json.loads(parent['settings'])['errorWorkflow'] == ids['errors']
    assert next(w for w in report['workflows'] if w['id'] == ids['errors'])['active']
    report['failure_endpoint_after_unpublish'] = lab.request(15678, '/webhook/wonmin-p13-failure', {})['status']
    assert report['failure_endpoint_after_unpublish'] == 404
    payload = {'request_id': 'wm-final-restored', 'requester': '박서연', 'title': 'VPN 확인',
               'category': 'network', 'priority': 'normal', 'reason': 'no_evidence'}
    report['normal_auth_without_key'] = lab.request(15678, '/webhook/oke-handoff', payload)['status']
    assert report['normal_auth_without_key'] in (401, 403)
    report['normal_handoff'] = lab.request(15678, '/webhook/oke-handoff', payload, {'X-Team-Key': values['N8N_WEBHOOK_KEY']})
    assert report['normal_handoff']['body']['ok'] is True
    report['local_llm'] = lab.request(15678, '/webhook/wonmin-local-llm', {'probe': 'local_llm'}, timeout=150)
    assert report['local_llm']['status'] == 200 and report['local_llm']['body']['ok'] is True
    report['backend_live'] = lab.request(18000, '/health/live')
    report['backend_ready'] = lab.request(18000, '/health/ready')
    assert report['backend_live']['status'] == 200
    assert report['backend_ready']['status'] == 404  # This peer revision exposes only /health/live.
    for endpoint, body in [('tickets', {'key':'wm-final-api','title':'합성','requester':'박서연','category':'network','priority':'normal'}),
                           ('alerts', {'workflow':'oke-errors','node':'lab','message':'합성','severity':'high'}),
                           ('dlq', {'request_id':None,'workflow':'oke-errors','node':'lab','reason':'unexpected','safe_payload':{}})]:
        report['backend_' + endpoint] = lab.request(18000, '/' + endpoint, body, {'X-Api-Key': values['INTERNAL_API_KEY']})
        assert report['backend_' + endpoint]['status'] == 501
    result = subprocess.run(lab.COMPOSE + ['exec','-T','-e','OKE_RUN_DB_TESTS=1','backend','uv','run','pytest','-q','tests/integration'],
                            capture_output=True, text=True, timeout=90)
    report['actual_postgres_tests'] = {'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
    assert result.returncode == 0
    report['backend_commit'] = json.loads((OWN / '.runtime/provenance.json').read_text())['jihye_commit']
    report['runtime_restored'] = True
    report['versions'] = {'n8n':lab.compose('exec','-T','n8n','n8n','--version').strip(),
                          'docker':lab.command(['docker','version','--format','{{.Server.Version}}']).strip(),
                          'compose':lab.command(['docker','compose','version','--short']).strip()}
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    for secret in values.values():
        if len(secret) >= 16:
            assert secret not in text
    with (OWN / 'runs/ubuntu-final-restoration.json').open('x') as target:
        target.write(text)
    print(json.dumps({'restored':True,'local_llm':report['local_llm'],'postgres_exit':result.returncode}))


if __name__ == '__main__':
    main()
