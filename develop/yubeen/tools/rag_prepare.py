"""P0-1 원본 대장 수집 어댑터. API 실행에는 사용자의 별도 승인이 필요하다."""
import argparse
import copy
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import statistics
from urllib import error, parse, request

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {'password-policy', 'remote-work-vpn', 'email-and-documents',
            'device-issue-return', 'software-usage', 'security-incident',
            'meeting-room', 'privacy'}


class InventoryError(ValueError):
    """고정된 오류 코드만 사용하며, 외부 응답 메시지나 데이터는 포함하지 않는다."""


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalize(text):
    return text.replace('\r\n', '\n').replace('\r', '\n')


def sections(text):
    """빈 절을 포함해 원본의 절 목록을 조사한다. 청크는 생성하지 않는다."""
    result, body, title, fence = [], [], None, None
    for line in normalize(text).splitlines(keepends=True):
        if fence:
            body.append(line)
            if re.fullmatch(r' {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}[ \t]*\n?', line):
                fence = None
            continue
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)', line)
        if marker and not (marker[1][0] == '`' and '`' in marker[2]):
            fence = marker[1]
            body.append(line)
            continue
        heading = re.match(r'^ {0,3}##(?:[ \t]+(.*?)|[ \t]*)\n?$', line)
        if heading:
            if title is not None:
                result.append((title, len(''.join(body))))
            elif ''.join(body).strip():
                result.append(('서문', len(''.join(body))))
            title = re.sub(r'[ \t]+#+[ \t]*$', '', heading[1] or '').strip()
            body = []
        else:
            body.append(line)
    if title is not None:
        result.append((title, len(''.join(body))))
    else:
        result.append(('본문', len(''.join(body))))
    return result


def validate_list(value):
    if not isinstance(value, dict) or not isinstance(value.get('docs'), list):
        raise InventoryError('invalid_list_response')
    docs = value['docs']
    if any(not isinstance(d, dict) or not isinstance(d.get('name'), str)
           or not d['name'].strip() for d in docs):
        raise InventoryError('invalid_list_response')
    return docs


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def http_transport(url, headers, timeout):
    """GET 요청만 사용한다. 인증 정보가 전달되지 않도록 리다이렉트를 금지한다."""
    with request.build_opener(NoRedirect()).open(
            request.Request(url, headers=headers, method='GET'), timeout=timeout) as response:
        return response.status, response.read()


def safe_rows(rows, secrets=()):
    """출력 허용 필드만 복사하고 직렬화 전에 민감정보를 제거한다."""
    secrets = tuple(value for value in secrets if value)

    def clean(value):
        if isinstance(value, str):
            for secret in secrets:
                value = value.replace(secret, '[REDACTED]')
            return value
        if isinstance(value, (list, tuple)):
            return [clean(item) for item in value]
        if isinstance(value, dict):
            return {clean(key): clean(item) for key, item in value.items()}
        return value

    result = []
    fields = ('doc_key', 'source_url', 'title', 'retrieved_at', 'access_level',
              'permission_evidence', 'source_hash', 'body_length', 'sections', 'reasons')
    for original in rows:
        row = {field: copy.deepcopy(original[field]) for field in fields}
        if row['access_level'] != 'all':
            row['title'] = '[非공개]'
            row['sections'] = [('[非공개]', length) for _, length in row['sections']]
        result.append(clean(row))
    return result


def collect_api(environ=None, transport=None, clock=now, processor=None, allow_network=False, no_auth=False):
    if transport is None and not allow_network:
        raise InventoryError('api_network_not_authorized')
    environ = os.environ if environ is None else environ
    transport = http_transport if transport is None else transport
    base, key = environ.get('DATA_API_URL', ''), environ.get('DATA_API_KEY', '')
    parsed = parse.urlsplit(base)
    if (parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise InventoryError('invalid_api_configuration')
    if no_auth:
        if (parsed.scheme != 'http' or parsed.netloc != 'data-api:8800'
                or parsed.path not in ('', '/') or key):
            raise InventoryError('invalid_api_configuration')
        headers = {}
    else:
        if not key or '\n' in key or '\r' in key:
            raise InventoryError('invalid_api_configuration')
        headers = {'X-Api-Key': key}

    def fetch(path):
        try:
            status, payload = transport(base.rstrip('/') + path, headers, 10)
            if status in (401, 403):
                raise InventoryError('authentication_failed')
            if status != 200:
                raise InventoryError('http_error')
            return json.loads(payload)
        except InventoryError:
            raise
        except error.HTTPError as exc:
            raise InventoryError('authentication_failed' if exc.code in (401, 403) else 'http_error') from None
        except (TimeoutError, socket.timeout):
            raise InventoryError('timeout') from None
        except error.URLError as exc:
            raise InventoryError('timeout' if isinstance(exc.reason, TimeoutError) else 'transport_error') from None
        except (json.JSONDecodeError, UnicodeError):
            raise InventoryError('invalid_json') from None
        except (OSError, ValueError, TypeError):
            raise InventoryError('transport_error') from None

    listed = fetch('/docs')
    docs = validate_list(listed)
    snapshot = {'list_response': listed, 'document_responses': {}, 'collection_errors': {},
                'retrieved_at': {}, 'mode': 'api_no_auth' if no_auth else 'api', 'list_retrieved_at': clock()}
    for name in dict.fromkeys(d['name'] for d in docs):
        try:
            snapshot['document_responses'][name] = fetch('/docs/' + parse.quote(name, safe=''))
        except InventoryError as exc:
            snapshot['collection_errors'][name] = str(exc)
        snapshot['retrieved_at'][name] = clock()
    if processor is not None:
        return processor(snapshot, secrets=(key, os.environ.get('DATA_API_KEY')))
    # 원문 해시와 권한은 원본으로 계산하고, 반환 스냅샷에는 안전한 대장만 남긴다.
    rows = safe_rows(inventory(snapshot, clock=clock), (key, os.environ.get('DATA_API_KEY')))
    return {'mode': snapshot['mode'], 'prepared_rows': rows}


def inventory(snapshot, clock=now):
    if not isinstance(snapshot, dict):
        raise InventoryError('invalid_snapshot')
    if 'prepared_rows' in snapshot:
        return copy.deepcopy(snapshot['prepared_rows'])
    docs = validate_list(snapshot.get('list_response'))
    responses = snapshot.get('document_responses')
    if not isinstance(responses, dict):
        raise InventoryError('invalid_snapshot')
    counts = Counter(d['name'] for d in docs)
    rows = []
    stamp = clock()
    for index, item in enumerate(docs):
        key = item['name']
        response = responses.get(key)
        row = dict(doc_key=key, source_url='/docs/' + parse.quote(key, safe=''), title=None,
                   retrieved_at=snapshot.get('retrieved_at', {}).get(key, stamp),
                   access_level=None, permission_evidence=[], source_hash=None,
                   body_length=None, sections=[], reasons=[])
        if counts[key] > 1:
            row['reasons'].append('duplicate_doc_key')
        if not isinstance(response, dict) or not isinstance(response.get('text'), str):
            row['reasons'].append('body_unavailable')
        else:
            text = normalize(response['text'])
            row.update(title=response.get('title'), source_hash=digest(text.encode()),
                       body_length=len(text), sections=sections(text))
            if response.get('name') != key:
                row['reasons'].append('identity_mismatch')
            if not isinstance(row['title'], str) or not row['title'].strip():
                row['title'] = None
                row['reasons'].append('title_missing')
            if not text.strip():
                row['reasons'].append('empty_document')
        collection_error = snapshot.get('collection_errors', {}).get(key)
        if collection_error:
            row['reasons'].append(collection_error if collection_error in
                {'authentication_failed', 'http_error', 'timeout', 'transport_error', 'invalid_json'} else 'collection_failed')
        levels = []
        for source, data, field in [('list_response', item, f'docs[{index}].access_level'),
                                    ('document_response', response, 'access_level')]:
            if isinstance(data, dict) and 'access_level' in data:
                level = data['access_level']
                levels.append(level)
                row['permission_evidence'].append({'source': source, 'field': field,
                    'value': level if level in ('all', 'it') else '[invalid]'})
        if not levels:
            if key in EXPECTED:
                row['access_level'] = 'all'
                row['permission_evidence'].append({'source': 'docs/DATA-AND-DB.md §4 + docs/EVALUATION-GUIDE.md §1',
                    'field': 'exact doc_key in eight standard policies', 'value': 'all'})
            else:
                row['reasons'].append('permission_unconfirmed')
        elif any(v not in ('all', 'it') for v in levels):
            row['reasons'].append('permission_unconfirmed')
        elif len(set(levels)) != 1:
            row['reasons'].append('permission_conflict')
        else:
            row['access_level'] = levels[0]
        rows.append(row)
    return rows


def render(snapshot, rows, snapshot_hash=None):
    safe = safe_rows(rows, (os.environ.get('DATA_API_KEY'),))
    missing = sorted(EXPECTED - {r['doc_key'] for r in safe})
    # 원본/자격증명이 아닌 안전한 대장 투영만 해시 입력으로 직렬화한다.
    snapshot_hash = digest(json.dumps(safe, ensure_ascii=False, sort_keys=True).encode())
    api_mode = snapshot.get('mode') in ('api', 'api_no_auth')
    auth_mode = ('명시된 고정 내부 origin http://data-api:8800, 인증 헤더 미전송'
                 if snapshot.get('mode') == 'api_no_auth' else 'X-Api-Key')
    source_status = ('실제 API 목록/상세 응답을 수집했으며 각 권한 메타데이터는 아래 항목별로 표시한다.'
                     if api_mode else 'Mock 입력이며 실제 API 응답 구조·권한은 미검증이다.')
    report = ('# P0-1 원본 대장\n\n'
        f'모드: {"api" if api_mode else "mock"}. {source_status}\n'
        f'입력 스냅샷 SHA-256 (안전한 대장 투영): {snapshot_hash}\n\n'
        '어댑터 지원 형태(실측 전): /docs → {docs:[{name,access_level?}]}, '
        '/docs/{name} → {name,title,text,access_level?}. 다른 구조는 거절하며 추측 변환하지 않는다.\n'
        f'인증 경로: {auth_mode}.\n'
        '해시: 전체 본문 CRLF/CR→LF, 나머지 공백 보존, UTF-8 SHA-256. '
        '절은 원문 순서이며 길이 0인 절도 보존한다. 청크 생성/빈 절 색인 판단은 하지 않는다.\n'
        '권한: 명시 메타데이터 우선, 충돌/미지 값 거절. 없으면 공통 확정 규정 8종의 정확한 키만 all 매핑. '
        '관리자 키 미확정은 거절한다. H-Y02의 별도 매핑표 제안은 확정 출처로 사용하지 않는다.\n\n'
        f'조사 {len(rows)}항목 / 후속 준비 가능 {sum(not r["reasons"] for r in rows)}항목 / '
        f'거절 {sum(bool(r["reasons"]) for r in rows)}항목. 색인 성공 건수 아님.\n'
        f'입력 목록 기준 누락 규정: {", ".join(missing) or "없음"}. '
        '실제 규정 8종·관리자 문서 확보: 미확인.\n\n'
        '```json\n' + json.dumps(safe, ensure_ascii=False, indent=2) + '\n```\n')
    return report


def section_ranges(text):
    """LF 원문의 반열린 문자 범위를 만든다. 빈 절과 공백도 분석에 보존한다."""
    text = normalize(text)
    headings, offset, fence = [], 0, None
    for line in text.splitlines(keepends=True):
        if fence:
            if re.fullmatch(r' {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}[ \t]*\n?', line):
                fence = None
        else:
            marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)', line)
            if marker and not (marker[1][0] == '`' and '`' in marker[2]):
                fence = marker[1]
            else:
                heading = re.match(r'^ {0,3}##(?:[ \t]+(.*?)|[ \t]*)\n?$', line)
                if heading:
                    title = re.sub(r'[ \t]+#+[ \t]*$', '', heading[1] or '').strip()
                    headings.append((offset, offset + len(line), title))
        offset += len(line)
    if not headings:
        return [{'section': '본문', 'start': 0, 'end': len(text), 'body_start': 0}]
    result = []
    if text[:headings[0][0]].strip():
        result.append({'section': '서문', 'start': 0, 'end': headings[0][0], 'body_start': 0})
    for index, (start, body_start, title) in enumerate(headings):
        result.append({'section': title, 'start': start if index or result else 0,
                       'end': headings[index + 1][0] if index + 1 < len(headings) else len(text),
                       'body_start': body_start})
    return result


def chunk_document(doc_key, title, text, access_level, method):
    """청크 content를 향후 임베딩 입력으로 그대로 사용한다. 외부 호출은 없다."""
    if access_level not in ('all', 'it'):
        raise InventoryError('permission_unconfirmed')
    text = normalize(text)
    spans = section_ranges(text)
    source_hash = digest(text.encode())
    pieces, excluded = [], []
    if method == 'section':
        for order, span in enumerate(spans):
            if text[span['body_start']:span['end']].strip():
                pieces.append((span['start'], span['end'], [order]))
            else:
                excluded.append(dict(span, reason='empty_section'))
    elif method == '300':
        for start in range(0, len(text), 300):
            end = min(start + 300, len(text))
            pieces.append((start, end, [i for i, span in enumerate(spans)
                                      if span['start'] < end and span['end'] > start]))
    else:
        raise InventoryError('invalid_chunking_method')
    chunks, rejected = [], []
    for start, end, orders in pieces:
        names = [spans[i]['section'] for i in orders]
        section = ' / '.join(names)
        prefix = title + '\n' + section + '\n'
        body = text[start:end]
        content = prefix + body
        if not body.strip():
            excluded.append({'start': start, 'end': end, 'reason': 'empty_body'})
            continue
        # 토크나이저 미설치 상태의 보수적 검토 기준이며 모델 한도 실측값이 아니다.
        if len(content.encode()) > 8000:
            rejected.append({'start': start, 'end': end, 'reason': 'oversized_content_review'})
            continue
        chunks.append({'doc_key': doc_key, 'access_level': access_level,
            'chunk_no': len(chunks), 'section': section, 'content': content,
            'content_hash': digest(content.encode()), 'body_length': len(body),
            'prefix_length': len(prefix), 'content_length': len(content),
            'metadata': {'chunking': method, 'chunking_version': 'p0-2-v1',
                'source_hash': source_hash, 'section_order': orders[0] if orders else None,
                'part_no': 0 if method == 'section' else start // 300,
                'source_range': [start, end], 'included_sections': names}})
    # 제외/거절 범위까지 포함한 원본 분할을 검사한다. 빈 절 제외는 손실과 구별한다.
    ranges = [c['metadata']['source_range'] for c in chunks]
    ranges += [[r['start'], r['end']] for r in excluded + rejected]
    ranges.sort()
    cursor, exact = 0, True
    for start, end in ranges:
        exact = exact and start == cursor
        cursor = end
    exact = exact and cursor == len(text)
    chunk_ranges = [c['metadata']['source_range'] for c in chunks]
    chunk_characters = sum(end - start for start, end in chunk_ranges)
    excluded_characters = sum(r['end'] - r['start'] for r in excluded)
    rejected_characters = sum(r['end'] - r['start'] for r in rejected)
    status = 'partial' if chunks and rejected else 'rejected' if not chunks else 'complete'
    reasons = ['oversized_content_review'] if rejected else ['no_content_chunks'] if not chunks else []
    return {'chunks': chunks, 'sections': spans, 'excluded': excluded, 'rejected': rejected,
            'status': status, 'reasons': reasons,
            'source_hash': source_hash, 'coverage_with_exclusions': exact,
            'order_and_ranges_valid': exact,
            'chunk_coverage': {'ranges': chunk_ranges, 'characters': chunk_characters,
                'source_characters': len(text),
                'ratio': chunk_characters / len(text) if text else None,
                'covers_entire_source': chunk_characters == len(text)},
            'coverage_accounting': {'source_characters': len(text),
                'chunk_characters': chunk_characters, 'excluded_characters': excluded_characters,
                'rejected_characters': rejected_characters,
                'all_ranges_accounted': exact}}


def length_stats(values):
    return {'min': min(values), 'median': statistics.median(values), 'max': max(values)} if values else '미측정'


def compare_snapshot(snapshot, secrets=()):
    """동일 원본에서 두 청킹을 계산하고 공개 가능한 통계와 매핑만 반환한다."""
    secrets = tuple(v for v in (*secrets, os.environ.get('DATA_API_KEY')) if v)
    rows = inventory(snapshot, clock=lambda: 'not-recorded-in-comparison')
    safe_inventory = safe_rows(rows, secrets)
    summary = []
    cohort_lengths = {method: {state: {'body': [], 'content': []} for state in ('complete', 'partial', 'rejected')} for method in ('section', '300')}
    for row, safe in zip(rows, safe_inventory):
        item = {'doc_key': safe['doc_key'], 'access_level': safe['access_level'],
                'source_hash': row['source_hash'], 'reasons': list(safe['reasons']),
                'status': 'rejected' if row['reasons'] else 'complete', 'methods': {}}
        if not row['reasons']:
            doc = snapshot['document_responses'][row['doc_key']]
            for method in ('section', '300'):
                result = chunk_document(row['doc_key'], doc['title'], doc['text'], row['access_level'], method)
                chunks = result['chunks']
                bucket = cohort_lengths[method][result['status']]
                bucket['body'].extend(c['body_length'] for c in chunks)
                bucket['content'].extend(c['content_length'] for c in chunks)
                samples = []
                for chunk in chunks[:3]:
                    # 본문은 공개 문서도 보고서에 넣지 않는다. 해시·범위로 역추적한다.
                    sample = {k: copy.deepcopy(chunk[k]) for k in ('chunk_no', 'section', 'content_hash', 'metadata')}
                    if row['access_level'] != 'all':
                        sample['section'] = '[非공개]'
                        sample['metadata']['included_sections'] = ['[非공개]'] * len(sample['metadata']['included_sections'])
                    sample['content'] = '[본문 비출력: 실제 값은 chunk_document 반환 content이며 content_hash로 추적]'
                    samples.append(sample)
                section_inventory = copy.deepcopy(result['sections'])
                if row['access_level'] != 'all':
                    for span in section_inventory:
                        span['section'] = '[非공개]'
                exclusions = [{k: span[k] for k in ('start', 'end', 'reason')} for span in result['excluded']]
                item['methods'][method] = {'chunk_count': len(chunks),
                    'status': result['status'], 'reasons': result['reasons'],
                    'chunk_coverage': result['chunk_coverage'],
                    'coverage_accounting': result['coverage_accounting'],
                    'excluded_ranges': exclusions,
                    'section_inventory': section_inventory,
                    'body_lengths': length_stats([c['body_length'] for c in chunks]),
                    'content_lengths': length_stats([c['content_length'] for c in chunks]),
                    'prefix_lengths': length_stats([c['prefix_length'] for c in chunks]),
                    'coverage_with_exclusions': result['coverage_with_exclusions'],
                    'order_and_ranges_valid': result['order_and_ranges_valid'],
                    'empty_sections_excluded': len(result['excluded']),
                    'rejected_ranges': result['rejected'], 'samples': samples}
            states = [m['status'] for m in item['methods'].values()]
            item['status'] = 'complete' if all(v == 'complete' for v in states) else 'rejected' if all(v == 'rejected' for v in states) else 'partial'
            for method, result in item['methods'].items():
                item['reasons'].extend(method + ':' + reason for reason in result['reasons'])
        summary.append(item)
    # 문자열을 직렬화하기 전에 키 반사값을 제거한다.
    def clean(value):
        if isinstance(value, str):
            for key in secrets:
                value = value.replace(key, '[REDACTED]')
            return value
        if isinstance(value, list):
            return [clean(v) for v in value]
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        return value
    summary = clean(summary)
    cohort_statistics = {}
    for method in ('section', '300'):
        cohort_statistics[method] = {}
        for state in ('complete', 'partial', 'rejected'):
            members = [row for row in summary if row['methods'].get(method, {}).get('status', 'rejected') == state]
            cohort_statistics[method][state] = {
                'document_count': len(members),
                'chunk_count': sum(row['methods'].get(method, {}).get('chunk_count', 0) for row in members),
                'body_lengths': length_stats(cohort_lengths[method][state]['body']),
                'content_lengths': length_stats(cohort_lengths[method][state]['content'])}
    snapshot_hash = digest(json.dumps(summary, ensure_ascii=False, sort_keys=True).encode())
    api_mode = snapshot.get('mode') in ('api', 'api_no_auth')
    return ('# P0-2 청킹 비교\n\n'
        f'모드: {"api" if api_mode else "mock"}. 실제 API·인증·원본 미검증.\n'
        f'동일 스냅샷의 안전한 비교 투영 SHA-256: {snapshot_hash}\n\n'
        '기본 section / 비교 본문 300 유니코드 문자, overlap=0. '
        '본문은 LF 정규화 전체 text이며 원본 ## 제목 행도 보존한다. '
        '두 방식의 접두어는 문서 제목 + LF + 포함 절 제목(여럿이면 / 연결) + LF. '
        'content는 접두어+원문 범위이며 향후 임베딩 입력과 동일하다. '
        '범위는 0부터 시작하는 반열린 문자 범위다. 빈 절은 분석에 남기고 기본 청크에서 제외한다.\n'
        '한도 검토: content UTF-8 8000바이트 초과는 별도 거절. '
        '토큰 한도 실측이나 최종 운영 한도가 아닌 보수적 개인 검토 기준이다. '
        'coverage_with_exclusions는 제외/거절까지 합친 범위 대장 검사다. 실제 청크 보존은 chunk_coverage로 별도 확인한다. '
        '본문·제목 원문은 출력하지 않고 비공개 표제도 가린다.\n'
        '실제 문서 길이·검색 품질·토큰·비용·시간: 미측정. 아래는 Mock 로컬 분석값이며 색인/검색 결과가 아니다.\n\n'
        '```json\n' + json.dumps(summary, ensure_ascii=False, indent=2) + '\n```\n\n'
        '## 상태별 분리 통계\n\n완전 성공·부분 생성·거절을 분리한다. 부분 생성 청크를 완전 성공 건수에 더하지 않는다.\n\n'
        '```json\n' + json.dumps(cohort_statistics, ensure_ascii=False, indent=2) + '\n```\n')


def main(argv=None, *, transport=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    inv = sub.add_parser('inventory')
    inv.add_argument('--source', choices=['mock', 'api'], required=True)
    inv.add_argument('--input', type=Path)
    inv.add_argument('--output', type=Path, required=True)
    inv.add_argument('--allow-network', action='store_true', help='승인받은 실제 API 실행에만 명시')
    inv.add_argument('--no-auth', action='store_true', help='고정된 내부 data-api origin의 무인증이 실제 확인된 경우에만 명시')
    comparison = sub.add_parser('compare-chunks')
    comparison.add_argument('--source', choices=['mock', 'api'], required=True)
    comparison.add_argument('--input', type=Path)
    comparison.add_argument('--baseline', choices=['section'], default='section')
    comparison.add_argument('--candidate', choices=['300'], default='300')
    comparison.add_argument('--output', type=Path, required=True)
    comparison.add_argument('--allow-network', action='store_true', help='승인받은 실제 API 실행에만 명시')
    comparison.add_argument('--no-auth', action='store_true', help='고정된 내부 data-api origin의 무인증이 실제 확인된 경우에만 명시')
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if not output.is_relative_to(ROOT):
        parser.error('output must be inside develop/yubeen')
    if args.source == 'mock' and args.input is None:
        parser.error('--input required for mock')
    try:
        if args.source == 'api':
            if args.command == 'compare-chunks':
                report = collect_api(transport=transport, processor=compare_snapshot,
                                     allow_network=args.allow_network, no_auth=args.no_auth)
                output.write_text(report, encoding='utf-8')
                return
            snapshot = collect_api(transport=transport, allow_network=args.allow_network, no_auth=args.no_auth)
            raw_hash = None
        else:
            raw = args.input.read_bytes()
            snapshot = json.loads(raw)
            raw_hash = None
        report = compare_snapshot(snapshot) if args.command == 'compare-chunks' else render(snapshot, inventory(snapshot), raw_hash)
        output.write_text(report, encoding='utf-8')
    except InventoryError as exc:
        code = 'api_network_not_authorized' if str(exc) == 'api_network_not_authorized' else 'inventory_failed'
        parser.exit(2, code + '\n')
    except (ValueError, KeyError, TypeError, OSError):
        parser.exit(2, 'Inventory failed; invalid input, configuration, HTTP response, or output. No upstream details logged.\n')


if __name__ == '__main__':
    main()
