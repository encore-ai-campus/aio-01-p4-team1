"""Offline evaluation only. No indexing or network. Fake numbers are not RAG quality."""
import math
import statistics
import hashlib
import re
from collections import Counter
from rag_search import validate_evidence

FIELDS = ('embedding_ms', 'db_ms', 'search_ms', 'embedding_tokens', 'chunk_count', 'cost')


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def safe_ref(value):
    """Report references use content hashes, never paths/URLs or arbitrary notes."""
    if value is not None and (not isinstance(value, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', value)):
        raise ValueError('invalid_source_reference')
    return value


def validate_answer_key(q):
    # Unfrozen drafts remain excluded; do not promote them by validating defaults.
    if q.get('source_verified') is not True or q.get('status') != 'frozen' or q.get('kind') in ('no_answer', 'admin_pending'):
        return
    quotes = q.get('verified_required_quotes')
    if not isinstance(quotes, list) or not quotes or not all(nonempty(v) for v in quotes):
        raise ValueError('invalid_required_quotes')
    if not all(nonempty(q.get(k)) for k in ('question', 'source_hash', 'expected_doc', 'expected_section')):
        raise ValueError('invalid_answer_key')


def section_hit(e, rank, record, expected, method, hashes):
    if e['section'] == expected:
        return True
    # Sidecar belongs to the evaluation record, not to the C03 response.
    sidecars = record.get('evidence_observations', [])
    if not isinstance(sidecars, list):
        raise ValueError('invalid_evidence_observations')
    matches = [s for s in sidecars if isinstance(s, dict) and s.get('rank') == rank]
    if len(matches) != 1:
        return False
    s = matches[0]; m = s.get('metadata', {})
    if not isinstance(m, dict):
        return False
    names = m.get('included_sections'); span = m.get('source_range')
    return (s.get('doc') == e['doc'] and s.get('content_hash') == hashlib.sha256(e['text'].encode()).hexdigest()
            and m.get('source_hash') == hashes.get(e['doc']) and hashes.get(e['doc']) is not None
            and m.get('chunking') == method and m.get('chunking_version') == 'p0-2-v1'
            and isinstance(names, list) and bool(names) and all(nonempty(n) for n in names)
            and e['section'] == ' / '.join(names) and expected in names
            and isinstance(span, list) and len(span) == 2 and all(type(n) is int for n in span)
            and 0 <= span[0] < span[1])


def measurement_record(record):
    values = {f: record.get(f) for f in FIELDS}
    provenance = {}
    supplied = record.get('measurement_provenance', {})
    if not isinstance(supplied, dict):
        raise ValueError('invalid_measurement_provenance')
    for field, value in values.items():
        stats([value])
        if field in ('embedding_tokens', 'chunk_count') and value is not None and type(value) is not int:
            raise ValueError('invalid_count')
        if field in ('embedding_tokens', 'chunk_count', 'cost') and value is not None:
            p = supplied.get(field)
            if not isinstance(p, dict) or p.get('kind') not in ('actual', 'estimated') or safe_ref(p.get('source_ref')) is None:
                raise ValueError('measurement_source_required')
            provenance[field] = {'kind': p['kind'], 'source_ref': p['source_ref']}
            if field == 'cost':
                currency = p.get('currency'); price = p.get('unit_price'); basis = safe_ref(p.get('calculation_ref'))
                if not isinstance(currency, str) or not re.fullmatch('[A-Z]{3}', currency):
                    raise ValueError('invalid_currency')
                if price is None and basis is None:
                    raise ValueError('cost_basis_required')
                stats([price])
                provenance[field].update(currency=currency, unit_price=price, calculation_ref=basis)
    return values, provenance


def stats(values):
    values = [v for v in values if v is not None]
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('invalid_measurement')
    ordered = sorted(values)
    return {'N': len(values), 'median': statistics.median(values) if values else None,
            'p95': ordered[math.ceil(.95 * len(values))-1] if values else None,
            'max': max(values) if values else None}


def compare_conditions(conditions):
    if set(conditions) != {'section', '300'}:
        raise ValueError('two_chunking_conditions_required')
    required = {'source_hashes', 'access_levels', 'model', 'dimensions', 'distance',
                'top_k', 'questions_version', 'repeats', 'overlap', 'environment', 'settings_version'}
    a, b = conditions['section'], conditions['300']
    if set(a) != required or set(b) != required or a != b:
        raise ValueError('comparison_conditions_mismatch')
    if not a['source_hashes'] or a['model'] != 'text-embedding-3-large' or a['dimensions'] != 3072 or a['distance'] != 'cosine' or a['top_k'] != 3 or a['overlap'] != 0:
        raise ValueError('invalid_comparison_conditions')
    if not all(nonempty(a[k]) for k in ('environment', 'settings_version', 'questions_version')):
        raise ValueError('missing_comparison_provenance')


def ratio(n, d):
    return {'numerator': n, 'denominator': d, 'value': n/d if d else None}


def evaluate(cases, repeats=3, bundle=None):
    if type(repeats) is not int or repeats < 1:
        raise ValueError('invalid_repeats')
    questions = cases['questions']
    for q in questions:
        validate_answer_key(q)
    if len({q['id'] for q in questions}) != len(questions):
        raise ValueError('duplicate_question_id')
    if bundle is not None:
        if bundle.get('mode') != 'fake':
            raise ValueError('only_fake_import_enabled')
        compare_conditions(bundle['conditions'])
        condition = bundle['conditions']['section']
        if condition['questions_version'] != cases['version'] or condition['repeats'] != repeats:
            raise ValueError('cases_or_repeats_mismatch')
    records = {} if bundle is None else bundle['records']
    expected_keys = {f"{method}:{q['id']}:{r}" for method in ('section','300') for q in questions for r in range(1,repeats+1)}
    if set(records) - expected_keys:
        raise ValueError('unknown_record')
    output = {'mode': 'preparation' if bundle is None else 'fake', 'actual_search_executed': False,
              'conditions': None if bundle is None else bundle['conditions'], 'methods': {}}
    for method in ('section', '300'):
        counts = Counter(); excluded = []; observations = []; measurements = {f:[] for f in FIELDS}
        groups = {f:{} for f in FIELDS}
        hits = sections = quotes = answers = no_answers = false_answers = leaks = leak_observed = answer_observed = 0
        for q in questions:
            frozen = q.get('source_verified') is True and q.get('status') == 'frozen' and bool(q.get('source_hash'))
            ready = frozen and bool(q.get('question')) and q.get('kind') != 'admin_pending'
            if q.get('kind') != 'no_answer':
                ready = ready and bool(q.get('expected_doc')) and bool(q.get('expected_section')) and bool(q.get('verified_required_quotes'))
            if bundle is not None and ready:
                hashes = bundle['conditions'][method]['source_hashes']
                ready = (q['source_hash'] in hashes.values() if q['kind'] == 'no_answer'
                         else hashes.get(q['expected_doc']) == q['source_hash']) and q['access_levels'] in bundle['conditions'][method]['access_levels']
            for repeat in range(1,repeats+1):
                key=f"{method}:{q['id']}:{repeat}"
                reason = 'admin_source_unavailable' if q.get('kind') == 'admin_pending' else 'answer_key_unfrozen'
                if not ready or key not in records:
                    excluded.append({'id':q['id'],'repeat':repeat,'reason':reason if not ready else 'not_executed'})
                    continue
                r=records[key]; status=r['http_status']; body=r['response']
                if status == 200 and body.get('ok') is True:
                    evidence=validate_evidence(body['evidence'])
                    if body.get('reason') != (None if evidence else 'no_evidence'):
                        raise ValueError('invalid_response_reason')
                    counts['normal' if evidence else 'empty'] += 1
                elif status == 503 and body == {'ok':False,'evidence':[],'reason':'search_unavailable'}:
                    evidence=[]; counts['failure'] += 1
                else:
                    raise ValueError('invalid_response')
                if q['kind'] == 'no_answer':
                    no_answers += 1
                    if type(r.get('incorrect_auto_answer')) is bool:
                        answer_observed += 1; false_answers += int(r['incorrect_auto_answer'])
                else:
                    answers += 1
                    matching=[e for e in evidence if e['doc']==q['expected_doc']]
                    hits += bool(matching)
                    sections += any(section_hit(e, rank, r, q['expected_section'], method,
                                                bundle['conditions'][method]['source_hashes'])
                                    for rank, e in enumerate(evidence, 1) if e['doc'] == q['expected_doc'])
                    quotes += bool(matching) and all(any(t in e['text'] for e in matching) for t in q['verified_required_quotes'])
                permissions = {} if bundle is None else bundle.get('doc_access',{})
                for e in evidence:
                    if e['doc'] in permissions:
                        leak_observed += 1; leaks += permissions[e['doc']] not in q['access_levels']
                measured, provenance = measurement_record(r)
                for f in FIELDS:
                    measurements[f].append(measured[f])
                    if measured[f] is not None:
                        p = provenance.get(f, {})
                        category = p.get('kind', 'observed') + ':' + p.get('currency', '')
                        groups[f].setdefault(category, []).append(measured[f])
                condition = bundle['conditions'][method]
                observations.append({'id':q['id'],'method':method,'repeat':repeat,'http_status':status,
                    'reason':body.get('reason'),'docs':[e['doc'] for e in evidence],
                    'evidence':[{'rank':rank, 'doc':e['doc'],
                                 'section':e['section'] if permissions.get(e['doc']) == 'all' else '[restricted_or_unknown]',
                                 'score':e['score']} for rank,e in enumerate(evidence,1)],
                    'measurements':measured, 'measurement_provenance':provenance,
                    'environment':condition['environment'],'model':condition['model'],
                    'settings_version':condition['settings_version'], 'source_ref':safe_ref(r.get('source_ref'))})
        output['methods'][method] = {'hit_at_3':ratio(hits,answers),'section_hit_at_3':ratio(sections,answers),
            'evidence_coverage':ratio(quotes,answers),'no_answer_incorrect':ratio(false_answers,answer_observed),
            'no_answer_attempts':no_answers,'permission_leaks':ratio(leaks,leak_observed),
            'response_counts':dict(counts),'measurements':{f:stats(v if len(groups[f]) <= 1 else []) for f,v in measurements.items()},
            'measurement_groups':{f:{kind:stats(v) for kind,v in g.items()} for f,g in groups.items()},
            'missing_measurements':{f:sum(x is None for x in v) for f,v in measurements.items()},
            'excluded':excluded,'observations':observations}
    return output
