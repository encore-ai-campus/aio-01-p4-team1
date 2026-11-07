#!/usr/bin/env python3
"""Automatic n8n Error Trigger against real app C05 storage in the private Ubuntu lab."""
import copy
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
import uuid

OWN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('c05', OWN / 'tools/test-c05-app-integration.py')
c05 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c05)
lab = c05.lab
CANARY = 'SYNTHETIC_ERRORS_APP_RAW_CANARY'
COUNTS = 'SELECT (SELECT count(*) FROM app.tickets) AS tickets,(SELECT count(*) FROM app.alerts) AS alerts,(SELECT count(*) FROM app.dlq) AS dlq'


def main():
    assert 'ubuntu' in Path('/etc/os-release').read_text().lower()
    private = dict(x.split('=', 1) for x in lab.ENVFILE.read_text().splitlines() if '=' in x)
    auth = {'X-Api-Key': private['INTERNAL_API_KEY']}
    team = {'X-Team-Key': private['N8N_WEBHOOK_KEY']}
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    idsfile = OWN / '.runtime/workflow-ids.json'
    ids = json.loads(idsfile.read_text())
    for key in ('errors_app', 'errors_app_parent', 'errors_app_guard'):
        ids.setdefault(key, 'wmerrapp' + secrets.token_hex(5))
    idsfile.write_text(json.dumps(ids, indent=2) + '\n')
    selected = {k: ids[k] for k in ('errors_app', 'errors_app_parent', 'errors_app_guard')}
    canonical = {k: v for k, v in ids.items() if k not in selected}
    report = {'scope': 'actual automatic n8n Error Trigger to ec6a735 FastAPI and PostgreSQL; controlled HTTP 503 faults',
              'cases': [], 'workflow_ids': selected, 'verdict': 'INCOMPLETE', 'restored': False}
    stage = 'preflight'
    failure = None
    imported = False

    def faults(plan):
        result = subprocess.run(c05.C05 + ['up', '-d', '--no-deps', '--force-recreate', 'c05-proxy'],
                    env={**os.environ, 'WONMIN_C05_FAULTS': json.dumps(plan)}, capture_output=True, text=True, timeout=60)
        assert result.returncode == 0, 'private fault proxy reconfiguration failed'
        c05.wait_http(18801, '/_lab/ops', auth)

    def ops():
        r = lab.request(18801, '/_lab/ops', headers=auth)
        assert r['status'] == 200
        return r['body']

    def save(name, **values):
        report['cases'].append({'case': name, **values})
        print(json.dumps({'case': name, 'verified': True}), flush=True)

    def import_workflows(workflows, basename):
        path = OWN / '.runtime/n8n-import' / basename
        path.write_text(json.dumps(workflows, ensure_ascii=False))
        path.chmod(0o600)
        lab.compose('exec', '-T', 'n8n', 'n8n', 'import:workflow', '--input=/fixtures/private/' + basename)

    def records():
        return lab.metadata('executions', selected)

    def storage(execution):
        key = 'n8n-execution:' + execution + ':unexpected-error'
        alerts = c05.query('SELECT event_key,workflow,node,message,severity FROM app.alerts WHERE event_key=:key', {'key': key})
        dlq = c05.query('SELECT request_id,execution_ref,workflow,node,reason,safe_payload FROM app.dlq WHERE execution_ref=:ref ORDER BY id', {'ref': execution})
        raw = json.dumps([alerts, dlq], ensure_ascii=False)
        assert CANARY not in raw and 'RAW_FAKE_PASSWORD' not in raw
        assert not any(v in raw for v in private.values() if len(v) >= 16)
        assert all(r['request_id'] is None and r['reason'] == 'unexpected' for r in dlq)
        return {'alerts': alerts, 'dlq': dlq, 'raw_error_absent': True}

    try:
        c05.wait_http(18001, '/health/ready')
        report['canonical_before'] = lab.metadata('workflows', canonical)
        report['main_db_before'] = c05.query(COUNTS, main_db=True)[0]
        report['test_db_before'] = c05.query(COUNTS)[0]
        marker = c05.c05('exec', '-T', 'c05-backend', 'uv', 'run', 'python', '-c',
                        'from pathlib import Path;print(Path(".deployment-source.json").read_text())')
        report['backend_source_commit'] = json.loads(marker)['commit']
        assert report['backend_source_commit'] == 'ec6a735ea93edacef97f15696bd84cd4e8055241'
        report['schema'] = c05.query('SELECT version_num FROM public.alembic_version')[0]['version_num']
        assert report['schema'] == '0005'
        source = OWN / 'workflows/oke-errors.json'
        error = json.loads(source.read_text())
        report['canonical_errors_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        error.update(id=ids['errors_app'], name='wonmin-errors-app-real', active=False)
        error['settings'].update(errorWorkflow='', saveDataErrorExecution='all', saveDataSuccessExecution='all', saveManualExecutions=False)
        creds = {'WONMIN_APP_STORE_AUTH': 'wonminLabStoreApp', 'WONMIN_PRACTICE_STORE_AUTH': 'wonminLabStorePractice'}
        for node in error['nodes']:
            ref = node.get('credentials', {}).get('httpHeaderAuth')
            if ref:
                ref['id'] = creds[ref['name']]
            if node['name'] == 'E02 Select Store':
                text = node['parameters']['jsCode']
                assert text.count('const mode = $env.SERVICE_MODE;') == 1
                assert text.count("$env.WONMIN_APP_STORE_URL || 'http://backend:8000'") == 1
                node['parameters']['jsCode'] = text.replace('const mode = $env.SERVICE_MODE;', "const mode = 'app';").replace(
                    "$env.WONMIN_APP_STORE_URL || 'http://backend:8000'", "'http://c05-proxy:8801'")
        hook = copy.deepcopy(json.loads((OWN / 'workflows/oke-handoff.json').read_text())['nodes'][0])
        hook['parameters']['responseMode'] = 'lastNode'
        hook['credentials']['httpHeaderAuth']['id'] = 'wonminLabTeam'
        hook['parameters']['path'] = 'wonmin-errors-app-parent'
        hook['webhookId'] = str(uuid.uuid5(uuid.NAMESPACE_URL, ids['errors_app_parent']))
        throw = {'id': 'private-error', 'name': 'H02 Validate and Map', 'type': 'n8n-nodes-base.code',
                 'typeVersion': 2, 'position': [220, 300],
                 'parameters': {'jsCode': "throw new Error('" + CANARY + " RAW_FAKE_PASSWORD=synthetic-only');"}}
        parent = {'id': ids['errors_app_parent'], 'name': 'wonmin-errors-app-parent', 'active': False,
                  'nodes': [hook, throw], 'connections': {hook['name']: {'main': [[{'node': throw['name'], 'type': 'main', 'index': 0}]]}},
                  'settings': {'executionOrder': 'v1', 'errorWorkflow': ids['errors_app'], 'saveDataErrorExecution': 'all', 'saveDataSuccessExecution': 'none'}}
        guard = copy.deepcopy(error)
        guard.update(id=ids['errors_app_guard'], name='wonmin-errors-app-guard', active=False)
        guard['nodes'] = [n for n in guard['nodes'] if n['type'] != 'n8n-nodes-base.errorTrigger']
        guard['connections'].pop('E01 Error Trigger')
        guard_hook = copy.deepcopy(hook)
        guard_hook.update(name='Private Guard Webhook', id='private-guard-webhook',
                          webhookId=str(uuid.uuid5(uuid.NAMESPACE_URL, ids['errors_app_guard'])))
        guard_hook['parameters']['path'] = 'wonmin-errors-app-guard'
        unwrap = {'id': 'private-unwrap', 'name': 'Private Unwrap Event', 'type': 'n8n-nodes-base.code', 'typeVersion': 2,
                  'position': [100, 100], 'parameters': {'jsCode': 'return [{json: $input.first().json.body}];'}}
        guard['nodes'].extend([guard_hook, unwrap])
        guard['connections'].update({guard_hook['name']: {'main': [[{'node': unwrap['name'], 'type': 'main', 'index': 0}]]},
                                    unwrap['name']: {'main': [[{'node': 'E02 Safe Error Context', 'type': 'main', 'index': 0}]]}})
        stage = 'publish_private_workflows'
        imported = True
        import_workflows([error, parent, guard], 'errors-app-test.json')
        for key in selected:
            lab.compose('exec', '-T', 'n8n', 'n8n', 'publish:workflow', '--id=' + ids[key])
        lab.compose('restart', 'n8n'); c05.wait_http(15678, '/healthz')
        faults({})
        for _ in range(30):
            denied = lab.request(15678, '/webhook/wonmin-errors-app-parent', {})['status']
            if denied in (401, 403):
                break
            assert denied in (404, 503)
            time.sleep(1)
        assert denied in (401, 403)
        metadata = lab.metadata('workflows', selected)
        assert json.loads(next(w for w in metadata if w['id'] == ids['errors_app_parent'])['settings'])['errorWorkflow'] == ids['errors_app']
        save('authentication_and_actual_parent_link', unauthenticated_status=denied, error_workflow_id=ids['errors_app'])

        first_parent = None
        for name, plan, expected in [('both_ok', {}, (True, True)), ('alerts_down', {'alerts': [503]}, (False, True)),
                    ('dlq_down', {'dlq': [503]}, (True, False)), ('all_down', {'alerts': [503], 'dlq': [503]}, (False, False)),
                    ('recovered', {}, (True, True))]:
            stage = name; faults(plan)
            baseline = max((int(r['id']) for r in records()), default=0)
            http = lab.request(15678, '/webhook/wonmin-errors-app-parent', {'probe': 'synthetic-only'}, team)
            assert http['status'] == 500, 'parent must remain failed'
            handler = None
            for _ in range(45):
                observed = [r for r in records() if int(r['id']) > baseline]
                matches = [r for r in observed if r['workflow_id'] == ids['errors_app'] and r['status'] == 'success' and r['outcome']]
                if matches:
                    handler = matches[0]; break
                time.sleep(0.4)
            assert handler, 'actual Error Trigger did not complete'
            parents = [r for r in observed if r['workflow_id'] == ids['errors_app_parent'] and r['status'] == 'error']
            assert len(parents) == 1 and handler['mode'] == 'error'
            ref = str(parents[0]['id'])
            assert handler['outcome']['execution_ref'] == ref and handler['outcome']['request_id'] is None
            assert (handler['outcome']['alerted'], handler['outcome']['dlq']) == expected
            stored = storage(ref)
            assert len(stored['alerts']) == int(expected[0]) and len(stored['dlq']) == int(expected[1])
            seen = ops()
            assert seen['calls'] == {'tickets': 0, 'alerts': 1, 'dlq': 1}
            time.sleep(1)
            assert len([r for r in records() if int(r['id']) > baseline and r['workflow_id'] == ids['errors_app']]) == 1
            save(name, parent_http_status=500, parent=parents[0], handler=handler, storage=stored, observed=seen, handler_count=1)
            if first_parent is None:
                first_parent = ref

        stage = 'reentry_guards'; faults({})
        for name, workflow in [('self_name', {'name': 'oke-errors', 'id': 'synthetic-other'}),
                               ('self_id', {'name': 'untrusted-name', 'id': ids['errors_app_guard']})]:
            body = {'workflow': workflow, 'execution': {'id': '999999999', 'error': {'message': CANARY}}}
            result = lab.request(15678, '/webhook/wonmin-errors-app-guard', body, team)
            assert result['status'] == 200 and result['body']['outcome'] == 'skipped_self'
            assert ops()['calls'] == {'tickets': 0, 'alerts': 0, 'dlq': 0}
            save(name, transport='authenticated probe of canonical guard code, not automatic Error Trigger', outcome=result['body'], observed=ops())

        stage = 'duplicate_alert_replay'
        event = {'workflow': {'name': 'unknown-parent', 'id': ids['errors_app_parent']},
                 'execution': {'id': first_parent, 'lastNodeExecuted': 'H02 Validate and Map', 'error': {'message': CANARY}}}
        replay = lab.request(15678, '/webhook/wonmin-errors-app-guard', event, team)
        assert replay['status'] == 200 and replay['body']['alerted'] is True and replay['body']['dlq'] is True
        stored = storage(first_parent)
        assert len(stored['alerts']) == 1 and len(stored['dlq']) == 2
        save(stage, transport='authenticated canonical-code event replay', outcome=replay['body'], storage=stored)

        stage = 'missing_execution_id'
        before = c05.query(COUNTS)[0]
        missing = lab.request(15678, '/webhook/wonmin-errors-app-guard', {'workflow': {}, 'trigger': {'error': {'message': CANARY}}}, team)
        assert missing['status'] == 200 and missing['body']['execution_ref'] is None and missing['body']['outcome'] == 'success'
        after = c05.query(COUNTS)[0]
        assert after['tickets'] == before['tickets'] and after['alerts'] == before['alerts'] + 1 and after['dlq'] == before['dlq'] + 1
        latest = c05.query('SELECT request_id,execution_ref,safe_payload FROM app.dlq ORDER BY id DESC LIMIT 1')[0]
        assert latest['request_id'] is None and latest['execution_ref'] is None and CANARY not in json.dumps(latest)
        save(stage, transport='authenticated canonical-code trigger-metadata probe', outcome=missing['body'], saved_dlq=latest)
        report['test_db_after'] = c05.query(COUNTS)[0]
        assert report['test_db_after']['tickets'] == report['test_db_before']['tickets']
        report['main_db_after'] = c05.query(COUNTS, main_db=True)[0]
        assert report['main_db_after'] == report['main_db_before']
    except Exception as error:
        failure = type(error).__name__
        report.update(failed_stage=stage, failure_type=failure)
    finally:
        try:
            faults({})
            if imported:
                for key in ('errors_app_parent', 'errors_app_guard'):
                    lab.compose('exec', '-T', 'n8n', 'n8n', 'unpublish:workflow', '--id=' + ids[key])
                restored = copy.deepcopy(parent)
                restored['nodes'][1]['parameters']['jsCode'] = 'return [{json: {restored: true}}];'
                import_workflows([restored], 'errors-app-parent-restored.json')
                lab.compose('restart', 'n8n'); c05.wait_http(15678, '/healthz')
                for _ in range(20):
                    disabled = {p: lab.request(15678, '/webhook/' + p, {}, team)['status'] for p in ('wonmin-errors-app-parent', 'wonmin-errors-app-guard')}
                    if all(s == 404 for s in disabled.values()):
                        break
                    time.sleep(0.5)
                assert all(s == 404 for s in disabled.values())
                report['disabled_probe_status'] = disabled
                report['final_workflows'] = lab.metadata('workflows', selected)
                assert all(not w['active'] for w in report['final_workflows'] if w['id'] != ids['errors_app'])
            report['canonical_after'] = lab.metadata('workflows', canonical)
            assert report['canonical_before'] == report['canonical_after']
            report['restored'] = True
            report['fault_proxy_normal'] = ops()
            report['health'] = {str(p): lab.request(p, path)['status'] for p, path in [(15678, '/healthz'), (18000, '/health/ready'), (18001, '/health/ready')]}
            assert all(s == 200 for s in report['health'].values())
            if failure is None:
                report['verdict'] = 'PASS_REAL_APP_AUTOMATIC_ERRORS_AND_INDEPENDENT_STORAGE'
        except Exception as error:
            report['cleanup_failure_type'] = type(error).__name__
            failure = failure or 'CleanupFailure'
        raw = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        assert not any(v in raw for v in private.values() if len(v) >= 16)
        path = OWN / 'runs' / ('errors-app-integration-' + stamp + '.json')
        with path.open('x') as output:
            output.write(raw)
        print(json.dumps({'report': path.name, 'verdict': report['verdict'], 'groups': len(report['cases']), 'restored': report['restored']}), flush=True)
    if failure:
        raise RuntimeError('private errors app test failed: ' + failure)


if __name__ == '__main__':
    main()
