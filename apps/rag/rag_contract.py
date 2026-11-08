"""Offline integration assertions; never changes the support workflow or route."""
import argparse
import hashlib
import json
from pathlib import Path

from rag_search import valid_levels, validate_evidence
from rag_db import write_new
from rag_verify import load_unique_json

ROUTES = {'자동 답변','보완 질문','담당자 이관','권한 없음','차단'}


def check(record, permissions):
    levels = record.get('access_levels')
    if not valid_levels(levels) or not permissions or any(v not in ('all','it') for v in permissions.values()):
        raise ValueError('invalid_permissions')
    status = record['search_status']; body = record['search_response']
    if status == 200 and body.get('ok') is True:
        evidence = validate_evidence(body.get('evidence'))
        if body.get('reason') != (None if evidence else 'no_evidence'):
            raise ValueError('invalid_reason')
    elif status in (400,401,503) and body == dict(ok=False,evidence=[],reason={400:'invalid_request',401:'unauthorized',503:'search_unavailable'}[status]):
        evidence = []
    else:
        raise ValueError('invalid_c03_response')
    for e in evidence:
        if permissions.get(e['doc']) not in levels:
            raise ValueError('evidence_permission_leak')
    support = record.get('support_response')
    observed = record.get('llm_evidence')
    if observed is not None:
        # This field must be the exact evidence list observed at the writer/verifier input.
        for e in validate_evidence(observed):
            if e not in evidence or permissions.get(e['doc']) not in levels:
                raise ValueError('llm_evidence_leak')
    if support is not None:
        required = {'request_id','route','answer','sources','ticket','agents','security'}
        if not required <= support.keys() or support['route'] not in ROUTES or not isinstance(support['sources'],list):
            raise ValueError('invalid_support_response')
        sources = [{k:e[k] for k in ('doc','section','score')} for e in evidence]
        for source in support['sources']:
            if source not in sources or permissions.get(source.get('doc')) not in levels:
                raise ValueError('source_permission_leak')
        if (status == 503 or status == 200 and not evidence) and support['route'] != '담당자 이관':
            raise ValueError('missing_handoff')
        if support['route'] == '자동 답변' and (not support['sources'] or not evidence):
            raise ValueError('ungrounded_auto_answer')
    return dict(ok=True, c03_checked=True, support_checked=support is not None,
                llm_boundary_observed=observed is not None,
                observation_ref='sha256:'+hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record',required=True); parser.add_argument('--permissions')
    parser.add_argument('--output',required=True)
    args = parser.parse_args(argv)
    try:
        supplied=load_unique_json(Path(args.record))
        record=supplied.get('record',supplied)
        permissions=load_unique_json(Path(args.permissions)) if args.permissions else supplied.get('doc_access')
        result = check(record,permissions)
        write_new(args.output,result)
        print(json.dumps(result)); return 0
    except Exception:
        print(json.dumps({'ok':False,'reason':'integration_contract_failed'})); return 1


if __name__ == '__main__':
    raise SystemExit(main())
