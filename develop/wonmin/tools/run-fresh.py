#!/usr/bin/env python3
"""Independent app-variant LLM runs; never a replacement for the official evaluator."""
import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import secrets
import time

OWN = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('c04', OWN / 'tools/test-c04-app-integration.py')
c04 = importlib.util.module_from_spec(spec); spec.loader.exec_module(c04)
c05, lab = c04.c05, c04.lab


def fresh_payload(case, prefix, round_number):
    digest = hashlib.sha256(f'{prefix}|{case["id"]}|{round_number}'.encode()).hexdigest()[:12]
    slug = re.sub('[^a-zA-Z0-9-]', '-', prefix)[:20]
    body = copy.deepcopy(case['input'])
    body['request_id'] = f'{slug}-{case["id"].lower()}-r{round_number}-{digest}'
    return body


def expectation_errors(case, reply):
    errors = []
    expected = case['expect']; body = reply.get('body')
    if reply.get('status') != expected['http_status']:
        errors.append('http_status')
    for path, wanted in expected.get('equals', {}).items():
        actual = body
        for key in path.split('.'):
            actual = actual.get(key) if isinstance(actual, dict) else None
        if type(actual) is not type(wanted) or actual != wanted:
            errors.append(path)
    if expected.get('route_in') and (not isinstance(body, dict) or body.get('route') not in expected['route_in']):
        errors.append('route_in')
    return errors


def latency_summary(samples):
    if not samples:
        raise ValueError('latency needs at least one attempt')
    values = sorted(s['seconds'] for s in samples)
    return {'n':len(values), 'failed':sum(not s['passed'] for s in samples),
            'p50_seconds':values[math.ceil(len(values)*0.5)-1], 'p95_seconds':values[math.ceil(len(values)*0.95)-1],
            'max_seconds':values[-1], 'method':'nearest-rank; all attempts including failures'}


def write_new_json(path, report, secret_values):
    raw = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if any(v in raw for v in secret_values if len(v) >= 16):
        raise ValueError('refuse secret output')
    with path.open('x') as output:
        output.write(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', default='cases/team-llm.json')
    parser.add_argument('--webhook', default='wonmin-c04-support-app', choices=['wonmin-c04-support-app'])
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument('--prefix')
    parser.add_argument('--case', dest='case_id')
    parser.add_argument('--bench', action='store_true')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if not 1 <= args.repeat <= 10:
        parser.error('repeat must be 1..10')
    output = (OWN / args.output).resolve()
    if output.parent != OWN / 'runs' or output.suffix != '.json' or output.exists():
        parser.error('output must be a new JSON file directly under own runs')
    suite_path = (OWN / args.suite).resolve()
    if not suite_path.is_relative_to(OWN / 'cases'):
        parser.error('suite must be inside own cases')
    suite = json.loads(suite_path.read_text())
    source_path = OWN / 'cases/team.json'
    assert suite['source_sha256'] == hashlib.sha256(source_path.read_bytes()).hexdigest()
    original = {c['id']:c for c in json.loads(source_path.read_text())['cases']}
    assert all(c == original[c['id']] for c in suite['cases']), 'original input and expectations must remain unchanged'
    cases = [c for c in suite['cases'] if not args.case_id or c['id'] == args.case_id]
    if not cases:
        parser.error('no selected cases')
    assert 'ubuntu' in Path('/etc/os-release').read_text().lower()
    prefix = args.prefix or 'llm-' + datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S') + '-' + secrets.token_hex(2)
    private = dict(x.split('=',1) for x in lab.ENVFILE.read_text().splitlines() if '=' in x)
    ids = json.loads((OWN / '.runtime/workflow-ids.json').read_text())
    selected = {k:ids[k] for k in ('c04_support_app','c04_handoff_app')}
    report = {'scope':suite['scope'], 'official_evaluation':False, 'source_suite_sha256':suite['source_sha256'],
              'suite_sha256':hashlib.sha256(suite_path.read_bytes()).hexdigest(), 'repeat':args.repeat, 'prefix':prefix,
              'bench':args.bench, 'unique_scenarios':len(cases), 'results':[], 'verdict':'INCOMPLETE'}
    samples = []
    stage = 'preflight'
    try:
        before = lab.metadata('workflows', ids); report['workflows_before'] = before
        assert all(w['active'] for w in before if w['id'] in selected.values())
        script = "const{DatabaseSync}=require('node:sqlite');const d=new DatabaseSync('/home/node/.n8n/database.sqlite',{readOnly:true});const n=JSON.parse(d.prepare('SELECT nodes FROM workflow_entity WHERE id=?').get(process.argv[1]).nodes);console.log(JSON.stringify(n.find(n=>n.name==='N06 Triage model').parameters));"
        model = json.loads(lab.compose('exec','-T','n8n','node','-e',script,ids['c04_support_app']))
        assert model['options']['responseFormat'] == 'json_object'
        report['model'] = model
        plan = lab.command(['docker','exec','wonmin-p13-lab-c05-proxy-1','python','-c','import os;print(os.environ["WONMIN_C05_FAULTS"])'])
        assert json.loads(plan) == {}, 'normal measurement requires no injected fault'
        report['main_db_before'] = c05.query(c04.COUNTS,main_db=True)[0]
        report['test_db_before'] = c05.query(c04.COUNTS)[0]
        all_execution_ids = []
        for case in cases:
            for round_number in range(1,args.repeat+1):
                stage = case['id'] + '-r' + str(round_number)
                payload = fresh_payload(case,prefix,round_number)
                key = payload['request_id']
                assert c05.query('SELECT count(*) AS n FROM app.tickets WHERE request_key=:key',{'key':key})[0]['n']==0, 'request key already used; choose a new prefix'
                attempts = []
                for duplicate_index in range(case['repeat']):
                    start = time.perf_counter()
                    reply = lab.request(15678,'/webhook/'+args.webhook,payload,{'X-Team-Key':private['N8N_WEBHOOK_KEY']},timeout=180)
                    seconds = round(time.perf_counter()-start,6)
                    errors = expectation_errors(case,reply)
                    body = reply['body']
                    if isinstance(body,dict):
                        if any(k not in body for k in ('request_id','route','answer','sources','ticket','agents','security')):
                            errors.append('required_response_fields')
                        if case['id']=='TM-02' and not all(word in body.get('answer','') for word in ['대상','오류','언제']):
                            errors.append('clarify_content')
                    attempts.append({'duplicate_index':duplicate_index,'request':payload,'reply':reply,'seconds':seconds,'errors':errors})
                for _ in range(30):
                    traces = [r for r in c04.traces(selected,0) if r['request_id']==key and r['status']=='success']
                    support = [r for r in traces if r['workflow_id']==ids['c04_support_app']]
                    if len(support)==len(attempts):break
                    time.sleep(0.2)
                errors = []
                if len(support)!=len(attempts):errors.append('missing_support_execution')
                for t in support:
                    if not t['triage'] or not t['triage']['executed'] or t['triage']['error'] is not None:
                        errors.append('actual_valid_llm_execution')
                    all_execution_ids.append(t['id'])
                tickets = c05.query('SELECT ticket_id,priority FROM app.tickets WHERE request_key=:key',{'key':key})
                alerts = c05.query('SELECT count(*) AS n FROM app.alerts WHERE event_key=:key',{'key':key+':ticket-created'})[0]['n']
                if case['id']=='TM-02':
                    if tickets or alerts:errors.append('clarification_stored_ticket_or_alert')
                else:
                    if len(tickets)!=1 or alerts!=1:errors.append('actual_ticket_alert_count')
                    if any(not isinstance(a['reply']['body'].get('ticket'),dict) or not a['reply']['body']['ticket'].get('ticket_id') for a in attempts):
                        errors.append('actual_ticket_id')
                if case['id']=='TM-06':
                    bodies=[a['reply']['body'] for a in attempts]
                    if not all(b.get('ticket') for b in bodies) or len({b['ticket']['ticket_id'] for b in bodies})!=1 or bodies[-1]['ticket']['duplicate'] is not True:
                        errors.append('sequential_duplicate')
                passed = not errors and not any(a['errors'] for a in attempts)
                for a in attempts:samples.append({'case':case['id'],'seconds':a['seconds'],'passed':passed and not a['errors']})
                report['results'].append({'case':case['id'],'round':round_number,'passed':passed,'errors':errors,
                                           'attempts':attempts,'traces':traces,'tickets':tickets,'alerts':alerts})
                print(json.dumps({'case':case['id'],'round':round_number,'passed':passed,'llm_executions':len(support)}),flush=True)
        assert len(all_execution_ids)==len(set(all_execution_ids)), 'reused execution is not an independent LLM run'
        report['actual_llm_executions']=len(all_execution_ids)
        report['summary']=latency_summary(samples)
        report['per_case_latency']={c['id']:latency_summary([s for s in samples if s['case']==c['id']]) for c in cases}
        report['main_db_after']=c05.query(c04.COUNTS,main_db=True)[0]
        report['test_db_after']=c05.query(c04.COUNTS)[0]
        report['workflows_after']=lab.metadata('workflows',ids)
        assert report['workflows_before']==report['workflows_after']
        assert report['main_db_before']==report['main_db_after']
        report['verdict']='PASS_SCOPED_APP_VARIANTS' if all(r['passed'] for r in report['results']) else 'FAIL_SCOPED_APP_VARIANTS'
    except Exception as error:
        report.update(failed_stage=stage,failure_type=type(error).__name__)
    finally:
        write_new_json(output,report,list(private.values()))
        print(json.dumps({'report':output.name,'verdict':report['verdict'],'rounds_recorded':len(report['results'])}),flush=True)
    if report['verdict']!='PASS_SCOPED_APP_VARIANTS':
        raise RuntimeError('scoped independent-run acceptance did not pass')


if __name__=='__main__':main()
