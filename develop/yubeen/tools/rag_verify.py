"""P1-1 Mock 색인 검증 CLI. 실제 API·임베딩·DB 연결을 생성하지 않는다."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from rag_index import MockStore, index_snapshot, load_settings

ROOT = Path(__file__).resolve().parents[1]


def mock_embed(content, model, dimensions):
    """결정적인 합성 벡터이며 실제 임베딩 또는 검색 품질 자료가 아니다."""
    seed = hashlib.sha256(content.encode()).digest()
    return {'model': model, 'embedding': [(seed[i % len(seed)] + 1) / 256 for i in range(dimensions)]}


def state_digest(store):
    """본문·벡터 원문 대신 저장 상태의 해시만 반환한다."""
    return hashlib.sha256(json.dumps(store.documents, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def verify_mock(snapshot=None):
    settings = load_settings()
    if snapshot is None:
        snapshot = json.loads((ROOT / 'cases/chunk-comparison-mock.json').read_text())
    store = MockStore()
    first = index_snapshot(snapshot, mock_embed, store, settings)
    before = state_digest(store)
    second = index_snapshot(snapshot, mock_embed, store, settings)
    unchanged = before == state_digest(store)
    embedding_inputs_match = True
    for document in store.documents.values():
        for chunk in document['chunks']:
            embedding_inputs_match &= chunk['content_hash'] == hashlib.sha256(chunk['content'].encode()).hexdigest()
    good = next((key for key in store.documents if store.documents[key]['access_level'] == 'all'), None)
    fault_checks = {'embedding_failure_preserves_previous': False,
                    'storage_failure_preserves_previous': False, 'retry_succeeds': False}
    if good:
        changed = copy.deepcopy(snapshot)
        changed['document_responses'][good]['text'] += '\n## 추가 절\n합성 변경 내용\n'
        previous = state_digest(store)
        calls = []

        def fail_after_one(content, model, dimensions):
            calls.append(True)
            if len(calls) == 2:
                raise RuntimeError('synthetic_embedding_fault')
            return mock_embed(content, model, dimensions)

        failed = index_snapshot(changed, fail_after_one, store, settings)
        fault_checks['embedding_failure_preserves_previous'] = (
            previous == state_digest(store) and failed['counts']['failed'] >= 1)
        store.fail_after_delete = True
        failed = index_snapshot(changed, mock_embed, store, settings)
        fault_checks['storage_failure_preserves_previous'] = (
            previous == state_digest(store) and failed['counts']['failed'] >= 1)
        store.fail_after_delete = False
        retried = index_snapshot(changed, mock_embed, store, settings)
        fault_checks['retry_succeeds'] = retried['counts']['indexed'] == 1
    checks = {'expected_first_counts': first['counts'] == {'indexed': 4, 'skipped': 0, 'rejected': 1, 'failed': 0},
              'expected_second_counts': second['counts'] == {'indexed': 0, 'skipped': 4, 'rejected': 1, 'failed': 0},
              'stored_documents_present': len(store.documents) == 4,
              'fault_scenarios_executed': good is not None,
              'repeat_unchanged': unchanged, 'content_hash_matches': embedding_inputs_match,
              'second_run_skips_all_stored': len(store.documents) > 0 and second['counts']['skipped'] == len(store.documents),
              'fk_and_unique_valid': bool(store.documents) and all(
                  len({c['chunk_no'] for c in doc['chunks']}) == len(doc['chunks'])
                  and all(c['document_id'] == doc['id'] and c['dimensions'] == 3072
                          and c['embedding_model'] == settings['embedding_model'] for c in doc['chunks'])
                  for doc in store.documents.values()), **fault_checks}
    return {'mode': 'mock', 'scenario': 'initial-and-repeat',
            'ok': bool(checks) and all(checks.values()),
            'first': first['counts'], 'second': second['counts'],
            'checks': checks, 'stored_documents': len(store.documents),
            'actual_api_embedding_db_n8n': 'not_executed'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    index = sub.add_parser('index')
    index.add_argument('--source', choices=['mock', 'api'], default='mock')
    index.add_argument('--scenario', choices=['initial-and-repeat'], required=True)
    index.add_argument('--output', type=Path)
    index.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    if args.source != 'mock':
        parser.exit(2, 'real_index_execution_not_enabled\n')
    if args.output and not args.output.resolve().is_relative_to(ROOT):
        parser.exit(2, 'output_outside_owner_directory\n')
    result = verify_mock()
    if args.output:
        old = args.output.read_text() if args.output.exists() else ''
        args.output.write_text(old + '\n\n## P1-1 Mock 색인 검증 실행 · 2026-11-04\n\n'
            '실제 색인 미실행. 아래는 합성 임베딩·저장 더블의 결과다.\n\n```json\n'
            + json.dumps(result, ensure_ascii=False, indent=2) + '\n```\n')
    print(json.dumps(result, ensure_ascii=False))
    if not result['ok']:
        parser.exit(1, 'mock_index_verification_failed\n')


if __name__ == '__main__':
    main()
