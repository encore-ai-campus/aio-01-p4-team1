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


def collect_api(environ=None, transport=None, clock=now):
    environ = os.environ if environ is None else environ
    transport = http_transport if transport is None else transport
    base, key = environ.get('DATA_API_URL', ''), environ.get('DATA_API_KEY', '')
    parsed = parse.urlsplit(base)
    if (parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.username
            or parsed.password or parsed.query or parsed.fragment or not key or '\n' in key or '\r' in key):
        raise InventoryError('invalid_api_configuration')

    def fetch(path):
        try:
            status, payload = transport(base.rstrip('/') + path, {'X-Api-Key': key}, 10)
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
                'retrieved_at': {}, 'mode': 'api', 'list_retrieved_at': clock()}
    for name in dict.fromkeys(d['name'] for d in docs):
        try:
            snapshot['document_responses'][name] = fetch('/docs/' + parse.quote(name, safe=''))
        except InventoryError as exc:
            snapshot['collection_errors'][name] = str(exc)
        snapshot['retrieved_at'][name] = clock()
    # 원문 해시와 권한은 원본으로 계산하고, 반환 스냅샷에는 안전한 대장만 남긴다.
    rows = safe_rows(inventory(snapshot, clock=clock), (key, os.environ.get('DATA_API_KEY')))
    return {'mode': 'api', 'prepared_rows': rows}


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
    report = ('# P0-1 원본 대장\n\n'
        f'모드: {"api" if snapshot.get("mode") == "api" else "mock"}. 실제 API 응답 구조·권한 및 관리자 문서 제공 여부 미검증.\n'
        f'입력 스냅샷 SHA-256 (안전한 대장 투영): {snapshot_hash}\n\n'
        '어댑터 지원 형태(실측 전): /docs → {docs:[{name,access_level?}]}, '
        '/docs/{name} → {name,title,text,access_level?}. 다른 구조는 거절하며 추측 변환하지 않는다.\n'
        '인증 헤더 X-Api-Key는 구현 가정이며 실제 data-api 확인 필요.\n'
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


def main(argv=None, *, transport=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    inv = sub.add_parser('inventory')
    inv.add_argument('--source', choices=['mock', 'api'], required=True)
    inv.add_argument('--input', type=Path)
    inv.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if not output.is_relative_to(ROOT):
        parser.error('output must be inside develop/yubeen')
    if args.source == 'mock' and args.input is None:
        parser.error('--input required for mock')
    try:
        if args.source == 'api':
            snapshot = collect_api(transport=transport)
            raw_hash = None
        else:
            raw = args.input.read_bytes()
            snapshot = json.loads(raw)
            raw_hash = None
        report = render(snapshot, inventory(snapshot), raw_hash)
        output.write_text(report, encoding='utf-8')
    except (ValueError, KeyError, TypeError, OSError):
        parser.exit(2, 'Inventory failed; invalid input, configuration, HTTP response, or output. No upstream details logged.\n')


if __name__ == '__main__':
    main()
