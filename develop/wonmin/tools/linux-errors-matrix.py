#!/usr/bin/env python3
"""Actual automatic Error Trigger matrix and restoration, scoped to the private Ubuntu lab."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error

OWN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('linux_lab', OWN / 'tools/linux-lab.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def wait_ready(port, path, headers=None):
    for _ in range(40):
        try:
            if lab.request(port, path, headers=headers, timeout=2)['status'] == 200:
                return
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(1)
    raise RuntimeError('lab service readiness timeout')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    assert Path(args.output).name == args.output and args.output.endswith('.json')
    assert 'ubuntu' in Path('/etc/os-release').read_text().lower()
    values = dict(line.split('=', 1) for line in lab.ENVFILE.read_text().splitlines() if '=' in line)
    ids = json.loads((OWN / '.runtime/workflow-ids.json').read_text())
    api_headers = {'X-Api-Key': values['INTERNAL_API_KEY']}
    report = {'scope': 'actual Ubuntu Compose n8n automatic failure; Mock sink vs peer backend explicitly separated',
              'workflow_ids': ids, 'cases': [], 'runtime_restored': False}

    def mock_faults(plan):
        env = {**os.environ, 'WONMIN_MOCK_FAULTS': json.dumps(plan)}
        r = subprocess.run(lab.COMPOSE + ['up', '-d', '--no-deps', '--force-recreate', 'mock-store'],
                           env=env, text=True, capture_output=True, timeout=60)
        assert r.returncode == 0, 'recreate only the private in-memory Mock failed'
        wait_ready(18800, '/_mock/ops', api_headers)

    def automatic_case(name, expected, sink):
        baseline = max((int(e['id']) for e in lab.metadata('executions', ids)), default=0)
        http = lab.request(15678, '/webhook/wonmin-p13-failure', {
            'request_id': 'wm-real-' + name, 'requester': '박서연', 'title': '비민감 오류 시험',
            'category': 'network', 'priority': 'normal', 'reason': 'no_evidence'})
        assert http['status'] == 500, 'controlled parent must fail through a production webhook'
        handler = None
        for _ in range(40):
            records = [e for e in lab.metadata('executions', ids) if int(e['id']) > baseline]
            completed = [e for e in records if e['workflow_id'] == ids['errors'] and e['status'] == 'success' and e['outcome']]
            if completed:
                handler = completed[-1]
                break
            time.sleep(0.5)
        assert handler, 'no completed actual Error Trigger execution'
        parents = [e for e in records if e['workflow_id'] == ids['failure'] and e['status'] == 'error']
        assert len(parents) == 1
        assert handler['mode'] == 'error'
        assert handler['outcome']['execution_ref'] == str(parents[0]['id'])
        assert (handler['outcome']['alerted'], handler['outcome']['dlq']) == expected
        # A failed sink must not create another recursive handler run.
        time.sleep(0.2)
        handlers = [e for e in lab.metadata('executions', ids) if int(e['id']) > baseline and e['workflow_id'] == ids['errors']]
        assert len(handlers) == 1
        item = {'case': name, 'sink': sink, 'parent_http_status': http['status'], 'parent': parents[0],
                'handler': handler, 'handler_count': len(handlers)}
        if sink == 'private_mock':
            item['observed'] = lab.request(18800, '/_mock/ops', headers=api_headers)['body']
            assert item['observed']['calls'] == {'tickets': 0, 'alerts': 1, 'dlq': 1}
        report['cases'].append(item)
        print(json.dumps({'case': name, 'parent_execution': parents[0]['id'], 'errors_execution': handler['id'],
                          'outcome': handler['outcome']['outcome']}), flush=True)

    try:
        for name, plan, expected in [
            ('both_ok', {}, (True, True)),
            ('alerts_down', {'alerts': [{'status': 503}]}, (False, True)),
            ('dlq_down', {'dlq': [{'status': 503}]}, (True, False)),
            ('all_down', {'alerts': [{'status': 503}], 'dlq': [{'status': 503}]}, (False, False)),
        ]:
            mock_faults(plan)
            automatic_case(name, expected, 'private_mock')

        app_compose = lab.COMPOSE + ['-f', str(OWN / 'deploy/compose.lab.app.yaml')]
        lab.command(app_compose + ['up', '-d', '--no-deps', '--force-recreate', 'n8n'])
        wait_ready(15678, '/healthz')
        automatic_case('actual_backend_unimplemented', (False, False), 'jihye_backend_real_http')
        report['backend_501_is_unimplemented_not_storage_success'] = True
        lab.compose('up', '-d', '--no-deps', '--force-recreate', 'n8n')
        wait_ready(15678, '/healthz')
        mock_faults({})

        # Restore the temporary parent from the original authenticated handoff, retaining real errorWorkflow ID.
        restored = json.loads((OWN / 'workflows/oke-handoff.json').read_text())
        restored['id'] = ids['failure']
        restored['settings']['errorWorkflow'] = ids['errors']
        for node in restored['nodes']:
            if node['name'] == 'H01 Handoff Webhook':
                node['parameters']['path'] = 'wonmin-p13-failure'
                node['webhookId'] = 'recovered-' + ids['failure']
            auth = node.get('credentials', {}).get('httpHeaderAuth')
            if auth:
                auth['id'] = {'WONMIN_APP_STORE_AUTH': 'wonminLabStoreApp', 'WONMIN_PRACTICE_STORE_AUTH': 'wonminLabStorePractice',
                              'WONMIN_X_TEAM_KEY': 'wonminLabTeam'}[auth['name']]
        target = OWN / '.runtime/n8n-import/restored-parent.json'
        target.write_text(json.dumps([restored], ensure_ascii=False))
        target.chmod(0o600)
        lab.compose('exec', '-T', 'n8n', 'n8n', 'import:workflow', '--input=/fixtures/private/restored-parent.json')
        lab.compose('exec', '-T', 'n8n', 'n8n', 'publish:workflow', '--id=' + ids['failure'])
        lab.compose('restart', 'n8n')
        wait_ready(15678, '/healthz')
        payload = {'request_id': 'wm-real-restored', 'requester': '박서연', 'title': 'VPN 복구 확인',
                   'category': 'network', 'priority': 'normal', 'reason': 'no_evidence'}
        # /healthz can become ready before credentials/webhooks finish initializing.
        for _ in range(30):
            status = lab.request(15678, '/webhook/wonmin-p13-failure', payload)['status']
            if status in (401, 403):
                break
            assert status in (404, 500, 503), 'unexpected unauthenticated response'
            time.sleep(1)
        report['restored_auth_rejects_no_key'] = status
        assert report['restored_auth_rejects_no_key'] in (401, 403)
        report['restored_parent_response'] = lab.request(15678, '/webhook/wonmin-p13-failure', payload,
                                                       {'X-Team-Key': values['N8N_WEBHOOK_KEY']})
        assert report['restored_parent_response']['status'] == 200 and report['restored_parent_response']['body']['ok'] is True
        lab.compose('exec', '-T', 'n8n', 'n8n', 'unpublish:workflow', '--id=' + ids['failure'])
        lab.compose('restart', 'n8n')
        wait_ready(15678, '/healthz')
        final_workflows = lab.metadata('workflows', ids)
        assert not next(w for w in final_workflows if w['id'] == ids['failure'])['active']
        report['final_workflows'] = final_workflows
        report['runtime_restored'] = True
        report['local_llm'] = lab.request(15678, '/webhook/wonmin-local-llm', {'probe': 'local_llm'}, timeout=150)
        assert report['local_llm']['status'] == 200 and report['local_llm']['body']['ok'] is True
        report['backend_live'] = lab.request(18000, '/health/live')
        report['backend_ready'] = lab.request(18000, '/health/ready')
        for endpoint, payload in [
            ('tickets', {'key': 'wm-real-api', 'title': '합성', 'requester': '박서연', 'category': 'network', 'priority': 'normal'}),
            ('alerts', {'workflow': 'oke-errors', 'node': 'lab', 'message': '비민감', 'severity': 'high'}),
            ('dlq', {'request_id': None, 'workflow': 'oke-errors', 'node': 'lab', 'reason': 'unexpected', 'safe_payload': {}}),
        ]:
            report['backend_' + endpoint] = lab.request(18000, '/' + endpoint, payload, api_headers)
            assert report['backend_' + endpoint]['status'] == 501

        db = subprocess.run(lab.COMPOSE + ['exec', '-T', '-e', 'OKE_RUN_DB_TESTS=1', 'backend',
                             'uv', 'run', 'pytest', '-q', 'tests/integration'], capture_output=True, text=True, timeout=90)
        assert db.returncode == 0
        report['actual_postgres_tests'] = {'exit': db.returncode, 'stdout': db.stdout, 'stderr': db.stderr}
        report['backend_commit'] = json.loads((OWN / '.runtime/provenance.json').read_text())['jihye_commit']
        report['versions'] = {'n8n': lab.compose('exec', '-T', 'n8n', 'n8n', '--version').strip(),
                              'docker': lab.command(['docker', 'version', '--format', '{{.Server.Version}}']).strip()}
    finally:
        if not report['runtime_restored']:
            # Never leave a deliberate unauthenticated failure endpoint published after a failed run.
            try:
                lab.compose('exec', '-T', 'n8n', 'n8n', 'unpublish:workflow', '--id=' + ids['failure'])
                lab.compose('restart', 'n8n')
                report['failed_run_parent_deactivated'] = True
            except Exception:
                report['failed_run_parent_deactivated'] = False
        # Always preserve a sanitized failure report as well, rather than silently manufacturing PASS.
        text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        for secret in values.values():
            if len(secret) >= 16:
                assert secret not in text, 'refuse secret output'
        with (OWN / 'runs' / args.output).open('x') as target:
            target.write(text)
        print(json.dumps({'report': args.output, 'cases_recorded': len(report['cases']), 'restored': report['runtime_restored']}), flush=True)


if __name__ == '__main__':
    main()
