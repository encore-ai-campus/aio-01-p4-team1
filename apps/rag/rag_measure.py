"""Collect real C03 measurements, merge two isolated indexing runs, evaluate."""
import argparse
import hashlib
import json
import os
import re
import time
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.parse import urlsplit

from rag_db import snapshot, compare, write_new, output_path
from rag_evaluate import evaluate
from rag_search import validate_evidence, valid_levels
from rag_verify import load_unique_json


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def http_search(body):
    url = os.environ.get('SEARCH_TEST_URL', '')
    parsed = urlsplit(url)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment or not os.getenv('SEARCH_TEAM_KEY')):
        raise ValueError('invalid_search_configuration')
    request = Request(url, data=json.dumps(body).encode(), method='POST',
        headers={'Content-Type':'application/json','X-Team-Key':os.environ['SEARCH_TEAM_KEY']})
    try:
        response = build_opener(NoRedirect()).open(request, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


def collect(cases, inventory, method, repeats, environment, search=http_search, clock=time.perf_counter,
            observe=None):
    evaluate(cases,repeats)  # Validate answer keys before any paid calls.
    if method not in ('section','300') or type(repeats) is not int or repeats < 1:
        raise ValueError('invalid_measurement_options')
    if not re.fullmatch('[A-Za-z0-9_-]{1,64}', environment):
        raise ValueError('invalid_environment_label')
    docs = inventory['documents']
    if not docs or any(not d['chunks'] or any(c['chunking'] != method for c in d['chunks']) for d in docs):
        raise ValueError('index_chunking_mismatch')
    levels = []; records = {}
    for q in cases['questions']:
        if not valid_levels(q.get('access_levels')):
            raise ValueError('invalid_case_access')
        if q['access_levels'] not in levels:
            levels.append(q['access_levels'])
    condition = dict(source_hashes={d['doc_key']:d['source_hash'] for d in docs}, access_levels=levels,
        model='text-embedding-3-large',dimensions=3072,distance='cosine',top_k=3,
        questions_version=cases['version'],repeats=repeats,overlap=0,environment=environment,
        settings_version='p1-1-v1')
    for q in cases['questions']:
        if q.get('status') != 'frozen' or q.get('source_verified') is not True or q.get('kind') == 'admin_pending':
            continue
        if q.get('kind') != 'no_answer' and condition['source_hashes'].get(q.get('expected_doc')) != q.get('source_hash'):
            raise ValueError('case_source_mismatch')
        if q.get('kind') == 'no_answer' and q.get('source_hash') not in condition['source_hashes'].values():
            raise ValueError('case_source_mismatch')
        for repeat in range(1,repeats+1):
            body = dict(request_id=f"eval-{method}-{repeat}",query=q['question'],type='evaluation',
                        access_levels=q['access_levels'],top_k=3)
            start = clock(); status, response = search(body); elapsed = (clock()-start)*1000
            if status == 200:
                evidence = validate_evidence(response.get('evidence'))
                if response.get('ok') is not True or response.get('reason') != (None if evidence else 'no_evidence'):
                    raise ValueError('invalid_search_response')
                if any(e['doc'] not in condition['source_hashes'] for e in evidence):
                    raise ValueError('unknown_evidence_document')
            elif status != 503 or response != dict(ok=False,evidence=[],reason='search_unavailable'):
                raise ValueError('invalid_search_status')
            ref = 'sha256:' + hashlib.sha256(json.dumps([body,status,response],sort_keys=True).encode()).hexdigest()
            records[f"{method}:{q['id']}:{repeat}"] = dict(http_status=status,response=response,
                search_ms=elapsed,source_ref=ref)
            if status == 200 and observe is not None:
                records[f"{method}:{q['id']}:{repeat}"]['evidence_observations'] = observe(evidence,q['access_levels'])
    if not records:
        raise ValueError('no_frozen_cases')
    return dict(mode='real', method=method, condition=condition,
                doc_access={d['doc_key']:d['access_level'] for d in docs},records=records)


def merge(a, b):
    runs = {a.get('method'):a,b.get('method'):b}
    if set(runs) != {'section','300'} or any(r.get('mode') != 'real' for r in runs.values()):
        raise ValueError('two_real_runs_required')
    if a['doc_access'] != b['doc_access']:
        raise ValueError('permissions_changed')
    bundle = dict(mode='real',conditions={m:r['condition'] for m,r in runs.items()},
                  doc_access=a['doc_access'],records={**a['records'],**b['records']})
    from rag_evaluate import compare_conditions
    compare_conditions(bundle['conditions'])
    return bundle


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    capture = sub.add_parser('collect')
    capture.add_argument('--cases',required=True); capture.add_argument('--method',choices=('section','300'),required=True)
    capture.add_argument('--repeats',type=int,default=3); capture.add_argument('--environment',required=True)
    capture.add_argument('--allow-external',action='store_true'); capture.add_argument('--output',required=True)
    combine = sub.add_parser('merge')
    combine.add_argument('--section',required=True); combine.add_argument('--chars',required=True); combine.add_argument('--output',required=True)
    report = sub.add_parser('report')
    report.add_argument('--cases',required=True); report.add_argument('--results',required=True)
    report.add_argument('--repeats',type=int,default=3); report.add_argument('--output',required=True)
    args = parser.parse_args(argv)
    try:
        if output_path(args.output).exists():
            raise ValueError('output_already_exists')
        if args.command == 'collect':
            if not args.allow_external or not os.getenv('DATABASE_URL'):
                raise ValueError('external_execution_not_authorized')
            import psycopg
            def inventory():
                with psycopg.connect(os.environ['DATABASE_URL'],connect_timeout=3,
                        options='-c default_transaction_read_only=on -c default_transaction_isolation=repeatable\\ read -c statement_timeout=10000') as db:
                    return snapshot(db)
            before = inventory()
            def observe(evidence, levels):
                sidecars=[]
                with psycopg.connect(os.environ['DATABASE_URL'],connect_timeout=3,
                        options='-c default_transaction_read_only=on -c statement_timeout=10000') as db:
                    with db.cursor() as cur:
                        for rank,e in enumerate(evidence,1):
                            content_hash=hashlib.sha256(e['text'].encode()).hexdigest()
                            cur.execute('SELECT c.metadata FROM rag.documents d JOIN rag.chunks c ON c.document_id=d.id WHERE d.doc_key=%s AND d.access_level=ANY(%s) AND c.content_hash=%s',
                                        (e['doc'],levels,content_hash))
                            rows=cur.fetchall()
                            if not rows:
                                raise ValueError('evidence_not_in_allowed_database')
                            sidecars.append(dict(rank=rank,doc=e['doc'],content_hash=content_hash,metadata=rows[0][0]))
                return sidecars
            result = collect(load_unique_json(Path(args.cases)),before,args.method,args.repeats,args.environment,
                             observe=observe)
            if not compare(before,inventory())['same_inventory']:
                raise ValueError('index_changed_during_measurement')
        elif args.command == 'merge':
            result = merge(load_unique_json(Path(args.section)),load_unique_json(Path(args.chars)))
        else:
            result = evaluate(load_unique_json(Path(args.cases)),args.repeats,load_unique_json(Path(args.results)))
        write_new(args.output,result)
        print(json.dumps({'ok':True,'mode':result['mode']}))
        return 0
    except Exception:
        print(json.dumps({'ok':False,'reason':'measurement_failed'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
