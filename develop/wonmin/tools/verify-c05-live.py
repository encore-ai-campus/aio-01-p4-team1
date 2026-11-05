#!/usr/bin/env python3
"""Read real backend responses and scoped PostgreSQL counts; never substitute the Mock."""
import concurrent.futures
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
import time
import urllib.error
import uuid

OWN = Path(__file__).resolve().parents[1]
ROOT = OWN.parents[1]
spec = importlib.util.spec_from_file_location('lab', OWN / 'tools/linux-lab.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def ready():
    for _ in range(40):
        try:
            if lab.request(15678, '/healthz')['status'] == 200:
                return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(1)
    raise RuntimeError('n8n readiness timeout')


def main():
    assert 'ubuntu' in Path('/etc/os-release').read_text().lower()
    values = dict(x.split('=', 1) for x in lab.ENVFILE.read_text().splitlines() if '=' in x)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    prefix = 'wm-c05-' + stamp
    headers = {'X-Api-Key': values['INTERNAL_API_KEY']}
    report = {'scope': 'real Jihye HTTP backend + actual PostgreSQL, not the practice Mock',
              'stamp': stamp, 'test_prefix': prefix, 'groups': {}, 'storage_verified': False}
    relative = ['app/api/deps.py', 'app/api/routes/tickets.py', 'app/api/routes/alerts.py', 'app/schemas/alerts.py']
    script = 'import hashlib,json;from pathlib import Path;print(json.dumps({p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ' + repr(relative) + '}))'
    report['deployed_source_hashes'] = json.loads(lab.compose('exec', '-T', 'backend', 'uv', 'run', 'python', '-c', script))
    assert all(hashlib.sha256((ROOT / 'develop/jihye' / p).read_bytes()).hexdigest() == h
               for p, h in report['deployed_source_hashes'].items()), 'backend must match the merged source'
    report['backend_live'] = lab.request(18000, '/health/live')
    assert report['backend_live']['status'] == 200

    def counts():
        code = '''import json,os,sys
from sqlalchemy import create_engine,text
p=sys.argv[1]
with create_engine(os.environ['DATABASE_URL']).connect() as c:
 c.execute(text('SET TRANSACTION READ ONLY'))
 result={
 'tickets':c.scalar(text('SELECT count(*) FROM app.tickets WHERE request_key LIKE :p'),{'p':p+'%'}),
 'alerts':c.scalar(text('SELECT count(*) FROM app.alerts WHERE event_key LIKE :p OR node=:node'),{'p':p+'%','node':p}),
 'dlq':c.scalar(text('SELECT count(*) FROM app.dlq WHERE request_id LIKE :p OR execution_ref LIKE :p'),{'p':p+'%'}),
 'employees_total':c.scalar(text('SELECT count(*) FROM app.employees')),
 'revision':c.scalar(text('SELECT version_num FROM public.alembic_version'))}
 print(json.dumps(result))
'''
        return json.loads(lab.compose('exec', '-T', 'backend', 'uv', 'run', 'python', '-c', code, prefix))

    def send(path, body, auth=headers):
        return lab.request(18000, path, body, auth)

    ticket = {'key': prefix + '-ticket', 'title': 'C05 합성 저장 검증', 'requester': '박서연', 'category': 'network', 'priority': 'normal'}
    alert = {'workflow': 'oke-handoff', 'node': prefix, 'message': 'C05 합성 알림 검증', 'severity': 'normal',
             'ticket_id': None, 'event_key': prefix + ':ticket-created'}
    dlq = {'request_id': prefix, 'workflow': 'oke-errors', 'node': prefix, 'reason': 'unexpected',
           'safe_payload': {'stage': 'unexpected'}, 'execution_ref': prefix + '-execution'}
    report['db_before'] = counts()
    for path, body in [('/tickets', ticket), ('/alerts', alert), ('/dlq', dlq)]:
        report['groups'][path + '_missing_key'] = send(path, body, {})
        assert report['groups'][path + '_missing_key']['status'] == 401
        report['groups'][path + '_invalid_key'] = send(path, body, {'X-Api-Key': 'synthetic-invalid-c05-key'})
    report['groups']['tickets_sequential_same_key'] = [send('/tickets', ticket) for _ in range(2)]
    report['groups']['tickets_high'] = send('/tickets', {**ticket, 'key': prefix + '-high', 'priority': 'high'})
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        report['groups']['tickets_concurrent_same_key_8'] = list(pool.map(
            lambda _: send('/tickets', {**ticket, 'key': prefix + '-concurrent'}), range(8)))
    report['groups']['alerts_sequential_same_event_key'] = [send('/alerts', alert) for _ in range(2)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        report['groups']['alerts_concurrent_same_event_key_8'] = list(pool.map(
            lambda _: send('/alerts', {**alert, 'event_key': prefix + ':concurrent'}), range(8)))
    without_key = {k: v for k, v in alert.items() if k != 'event_key'}
    report['groups']['alerts_event_key_absent_twice'] = [send('/alerts', without_key) for _ in range(2)]
    report['groups']['alerts_event_key_null_twice'] = [send('/alerts', {**alert, 'event_key': None}) for _ in range(2)]
    report['groups']['dlq_request_id'] = send('/dlq', dlq)
    report['groups']['dlq_null_request_id'] = send('/dlq', {**dlq, 'request_id': None})
    report['stored_response_model'] = json.loads(lab.compose('exec', '-T', 'backend', 'uv', 'run', 'python', '-c',
        'import json;from app.schemas.alerts import StoredResponse;print(json.dumps({"fields":list(StoredResponse.model_fields),"serialized_duplicate_ack":StoredResponse.model_validate({"stored":0,"count":1,"duplicate":True}).model_dump()}))'))

    # Test the actual app branch in a separate authenticated workflow; keep the current lab in practice mode.
    ids = json.loads((OWN / '.runtime/workflow-ids.json').read_text())
    clone_id = 'wmc05' + secrets.token_hex(5)
    clone = json.loads((OWN / '.runtime/n8n-import/team-workflows.json').read_text())
    clone = next(w for w in clone if w['name'] == 'oke-handoff')
    clone['id'], clone['name'], clone['active'] = clone_id, 'wonmin-c05-app-check-' + stamp, False
    clone['settings'].update(saveDataErrorExecution='none', saveDataSuccessExecution='none', saveManualExecutions=False)
    for node in clone['nodes']:
        if node['name'] == 'H01 Handoff Webhook':
            node['parameters']['path'] = 'wonmin-c05-app-check'
            node['webhookId'] = str(uuid.uuid5(uuid.NAMESPACE_URL, clone_id))
        if node['name'] == 'H03 Select Store':
            code = node['parameters']['jsCode']
            assert code.count('const mode = $env.SERVICE_MODE;') == 1
            node['parameters']['jsCode'] = code.replace('const mode = $env.SERVICE_MODE;', "const mode = 'app';")
    target = OWN / '.runtime/n8n-import/c05-live-check.json'
    target.write_text(json.dumps([clone], ensure_ascii=False)); target.chmod(0o600)
    report['n8n_app_check'] = {'workflow_id': clone_id, 'mode_override': 'app in this private deployment copy only'}
    try:
        lab.compose('exec', '-T', 'n8n', 'n8n', 'import:workflow', '--input=/fixtures/private/c05-live-check.json')
        lab.compose('exec', '-T', 'n8n', 'n8n', 'publish:workflow', '--id=' + clone_id)
        lab.compose('restart', 'n8n'); ready()
        for _ in range(30):
            response = lab.request(15678, '/webhook/wonmin-c05-app-check', {
                'request_id': prefix + '-n8n', 'requester': '박서연', 'title': 'C05 실제 app 저장 확인',
                'category': 'network', 'priority': 'normal', 'reason': 'no_evidence'},
                {'X-Team-Key': values['N8N_WEBHOOK_KEY']})
            if response['status'] not in (404, 500, 503):
                break
            time.sleep(1)
        report['n8n_app_check']['response'] = response
    finally:
        lab.compose('exec', '-T', 'n8n', 'n8n', 'unpublish:workflow', '--id=' + clone_id)
        lab.compose('restart', 'n8n'); ready()
        state = json.loads(lab.compose('exec', '-T', 'n8n', 'node', '-e',
            'const{DatabaseSync}=require("node:sqlite");const d=new DatabaseSync("/home/node/.n8n/database.sqlite",{readOnly:true});console.log(JSON.stringify(d.prepare("SELECT active FROM workflow_entity WHERE id=?").get(process.argv[1])));', clone_id))
        report['n8n_app_check']['cleanup_unpublished'] = state['active'] == 0
        assert report['n8n_app_check']['cleanup_unpublished']
    report['db_after'] = counts()
    report['blocked_requirements'] = ['real key verification', 'new/duplicate ticket ACK and single row',
        'alert duplicate field and same-key concurrency', 'DLQ HTTP200 stored ACK',
        'ticket retained after alert failure', 'real saved record persistence after restart']
    all_replies = [x for group in report['groups'].values() for x in (group if isinstance(group, list) else [group])]
    report['verdict'] = ('BLOCKED_BY_BACKEND_NOT_IMPLEMENTED' if any(r['status'] == 501 for r in all_replies)
                         else 'REVIEW_ACTUAL_ACK_AND_DB_RESULTS')
    report['http_status_counts'] = {str(status): sum(r['status'] == status for r in all_replies)
                                  for status in sorted({r['status'] for r in all_replies})}
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    assert not any(v in text for v in values.values() if len(v) >= 16)
    filename = 'c05-live-' + stamp + '.json'
    with (OWN / 'runs' / filename).open('x') as output:
        output.write(text)
    print(json.dumps({'report': filename, 'verdict': report['verdict'], 'status_counts': report['http_status_counts'],
        'db_before': report['db_before'], 'db_after': report['db_after'], 'n8n_app_check': report['n8n_app_check']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
