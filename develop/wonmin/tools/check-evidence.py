#!/usr/bin/env python3
"""Consistency audit for run-fresh reports; functional failures remain failures."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

OWN = Path(__file__).resolve().parents[1]
s = importlib.util.spec_from_file_location('fresh', OWN / 'tools/run-fresh.py')
fresh = importlib.util.module_from_spec(s); s.loader.exec_module(fresh)


def audit_report(report):
    errors, samples, execution_ids, round_keys = [], [], [], []
    results = report.get('results', [])
    if not results:
        errors.append('no_results')
    for group in results:
        attempts = group.get('attempts', [])
        keys = {a.get('request', {}).get('request_id') for a in attempts}
        if len(keys) != 1 or None in keys:
            errors.append('invalid_round_request_key')
        else:
            round_keys.append(next(iter(keys)))
        passed = bool(attempts) and not group.get('errors') and not any(a.get('errors') for a in attempts)
        if group.get('passed') is not passed:
            errors.append('group_verdict_mismatch')
        receipts = [t for t in group.get('traces', []) if t.get('triage') is not None]
        if len(receipts) != len(attempts):
            errors.append('llm_receipt_count_mismatch')
        for t in receipts:
            if not all(n in t.get('nodes', []) for n in ('N06 Triage model','N06 Triage Agent')):
                errors.append('missing_model_node_receipt')
            if t['triage'].get('executed') is not True or t['triage'].get('error') is not None:
                errors.append('missing_actual_llm_execution')
            if t.get('request_id') not in keys:
                errors.append('receipt_request_key_mismatch')
            execution_ids.append(str(t.get('id')))
        for a in attempts:
            seconds = a.get('seconds')
            if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
                errors.append('invalid_latency')
                continue
            samples.append({'seconds':seconds,'passed':passed and not a.get('errors')})
    if len(round_keys) != len(set(round_keys)):
        errors.append('reused_request_key_between_rounds')
    if len(execution_ids) != len(set(execution_ids)):
        errors.append('reused_llm_execution_id')
    if report.get('actual_llm_executions') != len(execution_ids):
        errors.append('llm_execution_count_mismatch')
    if samples and report.get('summary') != fresh.latency_summary(samples):
        errors.append('latency_summary_mismatch')
    functional_passed = bool(results) and all(r.get('passed') is True for r in results)
    wanted = 'PASS_SCOPED_APP_VARIANTS' if functional_passed else 'FAIL_SCOPED_APP_VARIANTS'
    if report.get('verdict') != wanted:
        errors.append('functional_verdict_mismatch')
    return {'integrity_errors':sorted(set(errors)), 'functional_passed':functional_passed,
            'attempts':len(samples), 'failed_attempts':sum(not s['passed'] for s in samples),
            'unique_round_keys':len(set(round_keys)), 'actual_llm_executions':len(execution_ids)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--index', default='runs/INDEX.md')
    p.add_argument('--report', action='append', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    index = (OWN / args.index).resolve(); output = (OWN / args.output).resolve()
    if not index.is_relative_to(OWN) or output.parent != OWN / 'runs' or output.suffix != '.json' or output.exists():
        p.error('index must be inside own folder and output a new runs JSON')
    text = index.read_text()
    audits = []
    for name in args.report:
        path = (OWN / name).resolve()
        if path.parent != OWN / 'runs' or path.suffix != '.json':
            p.error('reports must be directly inside own runs')
        raw = path.read_bytes(); report = json.loads(raw)
        result = audit_report(report)
        if '(' + path.name + ')' not in text:
            result['integrity_errors'].append('report_not_linked_from_index')
        for key, source in [('source_suite_sha256','cases/team.json'), ('suite_sha256','cases/team-llm.json')]:
            if report.get(key) != hashlib.sha256((OWN / source).read_bytes()).hexdigest():
                result['integrity_errors'].append('source_suite_hash_mismatch')
        audits.append({'report':path.name,'sha256':hashlib.sha256(raw).hexdigest(),**result})
    result = {'scope':'offline consistency only; not official evaluation or independent proof of live API/DB',
              'reports':audits,'integrity_passed':all(not a['integrity_errors'] for a in audits),
              'all_functional_passed':all(a['functional_passed'] for a in audits)}
    private = dict(x.split('=',1) for x in (OWN / '.runtime/lab.env').read_text().splitlines() if '=' in x)
    fresh.write_new_json(output,result,list(private.values()))
    print(json.dumps({'integrity_passed':result['integrity_passed'],'all_functional_passed':result['all_functional_passed'],'report':output.name}))
    if not result['integrity_passed']:
        raise RuntimeError('evidence has consistency errors')


if __name__=='__main__':main()
