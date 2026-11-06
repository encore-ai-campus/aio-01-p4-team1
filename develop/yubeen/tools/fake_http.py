"""Local n8n contract rehearsal. No PostgreSQL, OpenAI, or document I/O."""
import argparse
from http.server import ThreadingHTTPServer
import os
from threading import Thread

import index_http
import rag_prepare
import search_http


def fake_index(*_args, outcome='success', **_kwargs):
    if outcome == 'unavailable':
        raise RuntimeError('synthetic_failure')
    documents = [{'doc_key': key, 'status': 'indexed', 'chunk_count': 1, 'reason': None}
                 for key in sorted(rag_prepare.EXPECTED)]
    return {'ok': True, 'mode': 'mock', 'counts': {'indexed': 8, 'skipped': 0,
            'rejected': 0, 'failed': 0}, 'documents': documents}


def fake_search(body, trusted_access=False):
    # The production handler rejects unverified IT claims before this function.
    if trusted_access:
        return search_http.forbidden()
    if body['query'] == '__fake_503__':
        return search_http.unavailable()
    rows = [] if body['query'] == '__fake_empty__' else [
        {'doc': 'mock-public', 'section': '합성 절', 'text': '합성 검색 근거입니다.', 'score': 0.9}]
    return 200, {'ok': True, 'evidence': rows, 'reason': None if rows else 'no_evidence'}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Fake HTTP for personal n8n only')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--search-port', type=int, default=8765)
    parser.add_argument('--index-port', type=int, default=8766)
    parser.add_argument('--index-outcome', choices=('success', 'unavailable'), default='success')
    args = parser.parse_args(argv)
    if not os.environ.get('SEARCH_TEAM_KEY') or not os.environ.get('INDEX_TEAM_KEY'):
        parser.error('SEARCH_TEAM_KEY and INDEX_TEAM_KEY are required')
    if args.search_port == args.index_port:
        parser.error('ports must differ')
    index = ThreadingHTTPServer((args.host, args.index_port),
                                index_http.make_handler(lambda *a, **k: fake_index(*a, outcome=args.index_outcome, **k)))
    try:
        search = ThreadingHTTPServer((args.host, args.search_port), search_http.make_handler(fake_search))
    except Exception:
        index.server_close()
        raise
    worker = Thread(target=index.serve_forever, daemon=True)
    worker.start()
    try:
        print(f'FAKE_ONLY search={args.host}:{args.search_port} index={args.host}:{args.index_port}', flush=True)
        try:
            search.serve_forever()
        except KeyboardInterrupt:
            pass
    finally:
        search.server_close()
        index.shutdown()
        index.server_close()
        worker.join()


if __name__ == '__main__':
    main()
