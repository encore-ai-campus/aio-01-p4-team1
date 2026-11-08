#!/usr/bin/env python3
"""Measure independent authenticated workflow requests, including idle gaps. No hidden warm-up."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from uuid import uuid4
from live_check import (NORMAL_QUESTION, Session, assess_normal, load_settings,
                        local_commit, measure_response, validate_origin)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='https://aio-t1.isitsoft.kr:5678')
    parser.add_argument('--env-file', help='private file containing OKE_TEAM_KEY')
    parser.add_argument('--user', default='박서연', help='provided synthetic employee name')
    parser.add_argument('--repeats', type=int, default=3, choices=range(1, 6))
    parser.add_argument('--idle-seconds', type=float, default=20)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if not 0 <= args.idle_seconds <= 60:
        parser.error('idle seconds must be 0..60')
    output = Path(args.output)
    if output.exists():
        parser.error('output already exists')
    settings = load_settings(args.env_file)
    if not settings.get('OKE_TEAM_KEY'):
        parser.error('missing private setting: OKE_TEAM_KEY')
    report = {'schema': 'oke-workflow-latency-v1',
        'target': validate_origin(args.base_url), 'runner_source_commit': local_commit(),
        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'real n8n webhook; no frontend, API session, or DB linkage test',
        'condition': 'no hidden warm-up; no full-stack cold restart; first observation retained',
        'idle_seconds_between_requests': args.idle_seconds, 'records': [], 'errors': [], 'verdict': 'FAIL'}
    session = Session(report['target'])
    try:
        for index in range(args.repeats):
            if index:
                time.sleep(args.idle_seconds)
            request_id = 'audit-webhook-' + uuid4().hex
            status, body, elapsed = session.call('/webhook/oke-support', {
                'request_id': request_id, 'user': args.user,
                'question': NORMAL_QUESTION, 'attempt': 1}, headers={'X-Team-Key': settings['OKE_TEAM_KEY']})
            row = {'request_id': request_id, **measure_response(status, body, elapsed)}
            row['checks'] = assess_normal(row)
            report['records'].append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
        report['verdict'] = 'PASS' if all(all(r['checks'].values()) for r in report['records']) else 'FAIL'
    except Exception as error:
        report['errors'].append(type(error).__name__)
    report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'verdict': report['verdict'], 'output': str(output)}, ensure_ascii=False))
    return 0 if report['verdict'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
