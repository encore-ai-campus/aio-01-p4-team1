#!/usr/bin/env python3
"""Real n8n app workflow → controlled HTTP faults → FastAPI → isolated PostgreSQL."""
import concurrent.futures
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import urllib.error
import uuid

OWN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lab', OWN / 'tools/linux-lab.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)
C05 = lab.COMPOSE + ['-f', str(OWN / 'deploy/compose.c05.yaml')]


def c05(*args):
    return lab.command(C05 + list(args), timeout=120)


def wait_http(port, path, headers=None):
    for _ in range(45):
        try:
            if lab.request(port, path, headers=headers, timeout=3)['status'] == 200:
                return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(1)
    raise RuntimeError('private integration service readiness timeout')


def query(sql, params=None, *, main_db=False):
    code = '''import json,sys
from sqlalchemy import text
from app.db.session import create_db_engine
engine=create_db_engine()
with engine.connect() as c:
 c.execute(text('SET TRANSACTION READ ONLY'))
 rows=[dict(row._mapping) for row in c.execute(text(sys.argv[1]),json.loads(sys.argv[2]))]
 print(json.dumps(rows,default=str))
engine.dispose()
'''
    if main_db:
        result = lab.compose('exec', '-T', 'backend', 'uv', 'run', 'python', '-c', code, sql, json.dumps(params or {}))
    else:
        result = c05('exec', '-T', 'c05-backend', 'uv', 'run', 'python', '-c', code, sql, json.dumps(params or {}))
    return json.loads(result)


def main():
    assert 'ubuntu' in Path('/etc/os-release').read_text().lower()
    private = dict(x.split('=', 1) for x in lab.ENVFILE.read_text().splitlines() if '=' in x)
    auth = {'X-Api-Key': private['INTERNAL_API_KEY']}
    team = {'X-Team-Key': private['N8N_WEBHOOK_KEY']}
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    prefix = 'c05-' + stamp + '-' + secrets.token_hex(2)
    report = {'scope': 'actual app-mode FastAPI and PostgreSQL; controlled proxy failures only, no memory storage',
              'run_prefix': prefix, 'cases': [], 'verdict': 'INCOMPLETE',
              'fixture': 'provided six contract employees, isolated wonmin_c05_app database; not a live data-api seed'}
    idsfile = OWN / '.runtime/workflow-ids.json'
    ids = json.loads(idsfile.read_text())
    ids.setdefault('c05_app', 'wmc05live' + secrets.token_hex(5))
    idsfile.write_text(json.dumps(ids, indent=2) + '\n')
    case_name = 'preflight'

    def save_case(name, **values):
        report['cases'].append({'case': name, **values})
        print(json.dumps({'case': name, 'verified': True}), flush=True)

    def backend(path, body, headers=auth):
        return lab.request(18001, path, body, headers)

    def count(table, condition, params):
        assert table in ('tickets', 'alerts', 'dlq')
        return query('SELECT count(*) AS n FROM app.' + table + ' WHERE ' + condition, params)[0]['n']

    def ticket_count(key):
        return count('tickets', 'request_key=:key', {'key': key})

    def alert_count(event_key):
        return count('alerts', 'event_key=:key', {'key': event_key})

    def dlq_rows(key):
        return query('SELECT reason,safe_payload,execution_ref FROM app.dlq WHERE request_id=:key ORDER BY id', {'key': key})

    def faults(plan):
        env = {**os.environ, 'WONMIN_C05_FAULTS': json.dumps(plan)}
        result = subprocess.run(C05 + ['up', '-d', '--no-deps', '--force-recreate', 'c05-proxy'],
                                env=env, text=True, capture_output=True, timeout=60)
        assert result.returncode == 0, 'private proxy reconfiguration failed'
        wait_http(18801, '/_lab/ops', auth)

    def ops():
        response = lab.request(18801, '/_lab/ops', headers=auth)
        assert response['status'] == 200
        return response['body']

    def call_workflow(key, priority='normal'):
        response = lab.request(15678, '/webhook/wonmin-c05-app-real', {'request_id': key, 'requester': '박서연',
                    'title': 'C05 비민감 연결 시험', 'category': 'network', 'priority': priority, 'reason': 'no_evidence'}, team, timeout=20)
        assert response['status'] == 200, 'n8n app webhook response status'
        return response

    main_counts_sql = 'SELECT (SELECT count(*) FROM app.employees) AS employees,(SELECT count(*) FROM app.tickets) AS tickets,(SELECT count(*) FROM app.alerts) AS alerts,(SELECT count(*) FROM app.dlq) AS dlq'
    try:
        wait_http(18001, '/health/ready')
        report['main_db_before'] = query(main_counts_sql, main_db=True)[0]
        marker = c05('exec', '-T', 'c05-backend', 'uv', 'run', 'python', '-c',
                     'from pathlib import Path;print(Path(".deployment-source.json").read_text())')
        report['backend_source_commit'] = json.loads(marker)['commit']
        assert report['backend_source_commit'] == 'ec6a735ea93edacef97f15696bd84cd4e8055241'
        report['schema'] = query('SELECT version_num FROM public.alembic_version')[0]['version_num']
        assert report['schema'] == '0005'
        assert query('SELECT count(*) AS n FROM app.employees')[0]['n'] == 6
        payload = {'key': prefix + '-direct', 'title': 'C05 합성 요청', 'requester': '박서연', 'category': 'network', 'priority': 'normal'}
        alert = {'workflow': 'oke-handoff', 'node': prefix, 'message': 'C05 합성 알림', 'severity': 'normal', 'ticket_id': None}
        dlq = {'request_id': prefix, 'workflow': 'oke-errors', 'node': prefix, 'reason': 'unexpected',
               'safe_payload': {'stage': 'unexpected'}, 'execution_ref': prefix + '-direct'}

        case_name = 'authentication'
        denied = []
        for path, body in [('/tickets', payload), ('/alerts', alert), ('/dlq', dlq)]:
            for headers in ({}, {'X-Api-Key': 'synthetic-invalid-key'}):
                response = backend(path, body, headers)
                assert response['status'] == 401
                denied.append({'endpoint': path, 'status': response['status']})
        save_case(case_name, replies=denied)

        case_name = 'direct_ticket_new_and_duplicate'
        first, second = backend('/tickets', payload), backend('/tickets', payload)
        assert first['status'] == 201 and first['body']['duplicate'] is False
        assert second['status'] == 200 and second['body']['duplicate'] is True
        assert first['body']['ticket_id'] == second['body']['ticket_id'] and ticket_count(payload['key']) == 1
        save_case(case_name, responses=[first, second], rows=1)
        alert['ticket_id'] = first['body']['ticket_id']

        case_name = 'direct_ticket_concurrent_8'
        same = {**payload, 'key': prefix + '-direct-parallel'}
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            replies = list(pool.map(lambda _: backend('/tickets', same), range(8)))
        assert sum(r['status'] == 201 and r['body']['duplicate'] is False for r in replies) == 1
        assert sum(r['status'] == 200 and r['body']['duplicate'] is True for r in replies) == 7
        assert len({r['body']['ticket_id'] for r in replies}) == 1 and ticket_count(same['key']) == 1
        denied_owner = backend('/tickets', {**same, 'requester': '이준호'})
        assert denied_owner['status'] == 403 and ticket_count(same['key']) == 1
        save_case(case_name, responses=replies, rows=1, other_requester=denied_owner)

        case_name = 'direct_alert_new_duplicate_concurrent_and_no_key'
        keyed = {**alert, 'event_key': prefix + ':alert'}
        a, b = backend('/alerts', keyed), backend('/alerts', keyed)
        assert a['status'] == b['status'] == 200
        assert (a['body']['stored'], a['body']['duplicate']) == (1, False)
        assert (b['body']['stored'], b['body']['duplicate']) == (0, True)
        assert alert_count(keyed['event_key']) == 1
        parallel = {**alert, 'event_key': prefix + ':parallel-alert'}
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            replies = list(pool.map(lambda _: backend('/alerts', parallel), range(8)))
        assert all(r['status'] == 200 and type(r['body']['count']) is int and r['body']['count'] >= 1 for r in replies)
        assert sum(r['body']['stored'] for r in replies) == 1 and sum(r['body']['duplicate'] is True for r in replies) == 7
        assert alert_count(parallel['event_key']) == 1
        without_key = [backend('/alerts', alert) for _ in range(2)]
        null_key = [backend('/alerts', {**alert, 'event_key': None}) for _ in range(2)]
        assert all(r['status'] == 200 and r['body']['stored'] == 1 and r['body']['duplicate'] is False for r in without_key + null_key)
        assert count('alerts', 'node=:node AND event_key IS NULL', {'node': prefix}) == 4
        save_case(case_name, sequential=[a, b], concurrent=replies, no_key=without_key, null_key=null_key, no_key_rows=4)

        case_name = 'direct_dlq_ack_and_ticket_retained_after_real_alert_failure'
        d1 = backend('/dlq', dlq)
        d2 = backend('/dlq', {**dlq, 'request_id': None, 'execution_ref': prefix + '-null'})
        assert all(r['status'] == 200 and r['body']['stored'] == 1 for r in [d1, d2])
        assert count('dlq', 'execution_ref LIKE :prefix', {'prefix': prefix + '%'}) == 2
        failed_alert = backend('/alerts', {**alert, 'ticket_id': 'T-999999999'})
        assert failed_alert['status'] == 404 and ticket_count(payload['key']) == 1
        save_case(case_name, dlq=[d1, d2], alert_failure=failed_alert, ticket_rows_after=1)

        case_name = 'publish_private_app_workflow'
        workflow = json.loads((OWN / 'workflows/oke-handoff.json').read_text())
        report['workflow_source_sha256'] = hashlib.sha256((OWN / 'workflows/oke-handoff.json').read_bytes()).hexdigest()
        workflow.update(id=ids['c05_app'], name='wonmin-c05-app-real', active=False)
        workflow['settings'].update(errorWorkflow=ids['errors'], saveDataErrorExecution='none', saveDataSuccessExecution='none', saveManualExecutions=False)
        cred = {'WONMIN_X_TEAM_KEY': 'wonminLabTeam', 'WONMIN_APP_STORE_AUTH': 'wonminLabStoreApp',
                'WONMIN_PRACTICE_STORE_AUTH': 'wonminLabStorePractice'}
        for node in workflow['nodes']:
            auth_ref = node.get('credentials', {}).get('httpHeaderAuth')
            if auth_ref:
                auth_ref['id'] = cred[auth_ref['name']]
            if node['name'] == 'H01 Handoff Webhook':
                node['webhookId'] = str(uuid.uuid5(uuid.NAMESPACE_URL, ids['c05_app']))
                node['parameters']['path'] = 'wonmin-c05-app-real'
            if node['name'] == 'H03 Select Store':
                text = node['parameters']['jsCode']
                assert text.count('const mode = $env.SERVICE_MODE;') == 1
                assert text.count("$env.WONMIN_APP_STORE_URL || 'http://backend:8000'") == 1
                node['parameters']['jsCode'] = text.replace('const mode = $env.SERVICE_MODE;', "const mode = 'app';").replace(
                    "$env.WONMIN_APP_STORE_URL || 'http://backend:8000'", "'http://c05-proxy:8801'")
        target = OWN / '.runtime/n8n-import/c05-app-real.json'
        target.write_text(json.dumps([workflow], ensure_ascii=False)); target.chmod(0o600)
        lab.compose('exec', '-T', 'n8n', 'n8n', 'import:workflow', '--input=/fixtures/private/c05-app-real.json')
        lab.compose('exec', '-T', 'n8n', 'n8n', 'publish:workflow', '--id=' + ids['c05_app'])
        lab.compose('restart', 'n8n'); wait_http(15678, '/healthz')
        faults({})
        for _ in range(30):
            status = lab.request(15678, '/webhook/wonmin-c05-app-real', {})['status']
            if status == 403:
                break
            time.sleep(1)
        assert status == 403
        report['workflow_id'] = ids['c05_app']
        report['test_workflow_overrides'] = ['app mode and private proxy base in H03', 'private path/ID', 'local Credential IDs']

        case_name = 'n8n_app_normal_duplicate_high'
        key = prefix + '-workflow'
        a, b = call_workflow(key), call_workflow(key)
        assert a['body']['ok'] and b['body']['ok'] and a['body']['ticket']['duplicate'] is False and b['body']['ticket']['duplicate'] is True
        assert a['body']['ticket']['ticket_id'] == b['body']['ticket']['ticket_id']
        assert ticket_count(key) == 1 and alert_count(key + ':ticket-created') == 1
        high = call_workflow(prefix + '-high', 'high')
        assert high['body']['ok'] and high['body']['ticket']['priority'] == 'high'
        row = query('SELECT priority FROM app.tickets WHERE request_key=:key', {'key': prefix + '-high'})[0]
        assert row['priority'] == 'high'
        save_case(case_name, responses=[a, b, high], observed=ops(), ticket_rows=1, alert_rows=1)

        case_name = 'n8n_app_concurrent_8'
        faults({}); key = prefix + '-wf-parallel'
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            replies = list(pool.map(lambda _: call_workflow(key), range(8)))
        assert all(r['body']['ok'] for r in replies)
        assert len({r['body']['ticket']['ticket_id'] for r in replies}) == 1
        assert sum(r['body']['ticket']['duplicate'] is False for r in replies) == 1
        assert ticket_count(key) == alert_count(key + ':ticket-created') == 1
        save_case(case_name, responses=replies, observed=ops(), ticket_rows=1, alert_rows=1)

        for name, plan, ticket_exists, alerted, saved_dlq in [
            ('alerts_down', {'alerts': [503]}, True, False, True),
            ('tickets_down', {'tickets': [503]}, False, True, True),
            ('dlq_down', {'tickets': [503], 'dlq': [503]}, False, True, False),
            ('both_sinks_down', {'alerts': [503], 'dlq': [503]}, True, False, False),
            ('all_down', {'tickets': [503], 'alerts': [503], 'dlq': [503]}, False, False, False),
        ]:
            case_name = name; faults(plan); key = prefix + '-' + name
            response = call_workflow(key)
            body = response['body']
            assert body['ok'] is False and bool(body['ticket']) is ticket_exists
            assert body['alerted'] is alerted and body['dlq'] is saved_dlq
            assert body['reason'] == ('alerts_down' if ticket_exists else 'tickets_down')
            assert ticket_count(key) == int(ticket_exists)
            rows = dlq_rows(key)
            assert len(rows) == int(saved_dlq)
            for row in rows:
                text = json.dumps(row['safe_payload'], ensure_ascii=False)
                assert '박서연' not in text and 'C05 비민감 연결 시험' not in text
                assert private['INTERNAL_API_KEY'] not in text and private['N8N_WEBHOOK_KEY'] not in text
            observed = ops()
            assert observed['calls']['tickets'] <= 2 and observed['calls']['alerts'] == observed['calls']['dlq'] == 1
            save_case(name, response=response, ticket_rows=int(ticket_exists), dlq=rows, observed=observed)
            if name == 'alerts_down':
                faults({})
                recovered, duplicate = call_workflow(key), call_workflow(key)
                assert recovered['body']['ok'] and recovered['body']['ticket']['duplicate']
                assert duplicate['body']['ok'] and duplicate['body']['alerted']
                assert ticket_count(key) == alert_count(key + ':ticket-created') == 1
                save_case('alerts_recovered_same_ticket', responses=[recovered, duplicate], ticket_rows=1, alert_rows=1)

        case_name = 'transient_ticket_failure'
        faults({'tickets': [503, 0]}); key = prefix + '-flaky'
        recovered = call_workflow(key)
        observed = ops()
        assert recovered['body']['ok'] and ticket_count(key) == 1
        assert observed['calls']['tickets'] == 2 and observed['forwarded']['tickets'] == 1
        save_case(case_name, response=recovered, observed=observed, rows=1)

        case_name = 'postgres_restart_persistence'
        faults({})
        sql = 'SELECT (SELECT count(*) FROM app.tickets WHERE request_key LIKE :prefix) AS tickets,(SELECT count(*) FROM app.alerts WHERE event_key LIKE :prefix OR node=:node) AS alerts,(SELECT count(*) FROM app.dlq WHERE request_id LIKE :prefix OR execution_ref LIKE :prefix) AS dlq'
        params = {'prefix': prefix + '%', 'node': prefix}
        before = query(sql, params)[0]
        c05('restart', 'postgres'); wait_http(18001, '/health/ready'); wait_http(18000, '/health/ready')
        after = query(sql, params)[0]
        assert before == after and all(value > 0 for value in before.values())
        replay = call_workflow(prefix + '-workflow')
        assert replay['body']['ok'] and replay['body']['ticket']['duplicate']
        assert query(sql, params)[0] == after
        save_case(case_name, before=before, after=after, replay=replay)
        report['main_db_after'] = query(main_counts_sql, main_db=True)[0]
        assert report['main_db_before'] == report['main_db_after']
        report['verdict'] = 'PASS_REAL_APP_HTTP_DB_AND_WORKFLOW_INTEGRATION'
    except Exception as error:
        report['failed_stage'] = case_name
        report['failure_type'] = type(error).__name__
        raise
    finally:
        try:
            faults({})
            report['proxy_restored_to_forwarding'] = True
            if report['verdict'] != 'PASS_REAL_APP_HTTP_DB_AND_WORKFLOW_INTEGRATION':
                lab.compose('exec', '-T', 'n8n', 'n8n', 'unpublish:workflow', '--id=' + ids['c05_app'])
                lab.compose('restart', 'n8n'); wait_http(15678, '/healthz')
        finally:
            text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
            assert not any(value in text for value in private.values() if len(value) >= 16)
            name = 'c05-app-integration-' + stamp + '.json'
            with (OWN / 'runs' / name).open('x') as output:
                output.write(text)
            print(json.dumps({'report': name, 'verdict': report['verdict'], 'cases': len(report['cases'])}), flush=True)


if __name__ == '__main__':
    main()
