"""Approved local Markdown -> existing RAG index engine. No I/O on import."""
import argparse
import hashlib
import json
import os
from pathlib import Path

import rag_index
import rag_prepare


class LoadError(ValueError):
    pass


def build_snapshot(docs_dir, permissions_file):
    """Reject the entire batch before embedding or DB access if approval is incomplete."""
    root = Path(docs_dir).resolve(strict=True)
    if not root.is_dir():
        raise LoadError('invalid_docs_directory')
    try:
        from rag_verify import load_unique_json
        manifest = load_unique_json(Path(permissions_file))
    except (OSError, ValueError, UnicodeError):
        raise LoadError('invalid_permissions_manifest') from None
    approvals = manifest.get('documents') if isinstance(manifest, dict) else None
    if not isinstance(manifest, dict) or manifest.get('approval_status') != 'approved' or not isinstance(approvals, dict) or set(approvals) != rag_prepare.EXPECTED:
        raise LoadError('permissions_unconfirmed')
    files = list(root.iterdir())
    if len(files) != len(rag_prepare.EXPECTED) or {p.name for p in files} != {k + '.md' for k in rag_prepare.EXPECTED}:
        raise LoadError('document_set_mismatch')
    listed, responses = [], {}
    for key in sorted(rag_prepare.EXPECTED):
        item = approvals[key]
        if not isinstance(item, dict) or item.get('access_level') not in ('all', 'it') or not isinstance(item.get('sha256'), str) or len(item['sha256']) != 64:
            raise LoadError('permissions_unconfirmed')
        path = root / (key + '.md')
        if path.is_symlink() or not path.is_file():
            raise LoadError('invalid_document_file')
        try:
            raw = path.read_bytes()
            content = raw.decode('utf-8')
        except (OSError, UnicodeError):
            raise LoadError('invalid_document_file') from None
        if hashlib.sha256(raw).hexdigest() != item['sha256'].lower():
            raise LoadError('document_hash_mismatch')
        title = next((line[2:].strip() for line in content.splitlines() if line.startswith('# ') and line[2:].strip()), None)
        if not title:
            raise LoadError('document_title_missing')
        level = item['access_level']
        listed.append({'name': key, 'access_level': level})
        responses[key] = {'name': key, 'title': title, 'text': content, 'access_level': level}
    return {'list_response': {'docs': listed}, 'document_responses': responses}


def run_index(docs_dir, permissions_file, *, store, embedder, snapshot=None, comparison_chunking=None):
    snapshot = snapshot if snapshot is not None else build_snapshot(docs_dir, permissions_file)
    settings = rag_index.load_settings()
    if comparison_chunking is not None:
        if comparison_chunking not in ('section', '300'):
            raise LoadError('invalid_comparison_chunking')
        settings['chunking'] = comparison_chunking
    result = rag_index.index_snapshot(snapshot, embedder, store, settings,
                                     comparison=comparison_chunking is not None)
    for key, row in zip(sorted(rag_prepare.EXPECTED), result['documents']):
        row['doc_key'] = key
    result['ok'] = result['counts']['rejected'] == result['counts']['failed'] == 0
    return result


def execute(docs_dir, permissions_file, *, mode, allow_external=False, comparison_chunking=None):
    # Validate the entire source and permission batch before opening external services.
    snapshot = build_snapshot(docs_dir, permissions_file)
    if mode == 'fake':
        from rag_verify import mock_embed
        return run_index(docs_dir, permissions_file, store=rag_index.MockStore(), embedder=mock_embed, snapshot=snapshot, comparison_chunking=comparison_chunking)
    if mode != 'real' or not allow_external:
        raise LoadError('real_execution_not_authorized')
    dsn = os.environ.get('DATABASE_URL')
    if not dsn or not os.environ.get('OPENAI_API_KEY'):
        raise LoadError('runtime_not_configured')
    try:
        import psycopg
        from rag_search import OpenAIEmbeddingProvider
        with psycopg.connect(dsn, autocommit=False, connect_timeout=3) as connection:
            return run_index(docs_dir, permissions_file, store=rag_index.PostgresStore(connection),
                             embedder=OpenAIEmbeddingProvider(), snapshot=snapshot, comparison_chunking=comparison_chunking)
    except Exception:
        raise LoadError('index_unavailable') from None


def main(argv=None):
    parser = argparse.ArgumentParser(description='Index exactly eight approved Markdown files')
    parser.add_argument('--docs-dir', required=True)
    parser.add_argument('--permissions', required=True)
    parser.add_argument('--mode', choices=('fake', 'real'), default='fake')
    parser.add_argument('--allow-external', action='store_true')
    parser.add_argument('--comparison-chunking', choices=('section', '300'),
                        help='Explicit isolated evaluation index only; restore section afterwards')
    args = parser.parse_args(argv)
    try:
        result = execute(args.docs_dir, args.permissions, mode=args.mode, allow_external=args.allow_external,
                         comparison_chunking=args.comparison_chunking)
    except (LoadError, OSError) as exc:
        print(json.dumps({'ok': False, 'mode': args.mode, 'reason': str(exc) if isinstance(exc, LoadError) else 'invalid_document_file'}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
