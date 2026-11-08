"""Read-only PostgreSQL inventory and recovery comparison. No DDL or writes."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def snapshot(connection):
    # Caller opens one REPEATABLE READ, read-only transaction for a consistent view.
    with connection.cursor() as cur:
        cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
        extension = cur.fetchone()
        if not extension:
            raise ValueError('vector_extension_missing')
        cur.execute("SELECT format_type(atttypid,atttypmod) FROM pg_attribute WHERE attrelid='rag.chunks'::regclass AND attname='embedding' AND NOT attisdropped")
        if cur.fetchone() != ('vector(3072)',):
            raise ValueError('vector_type_mismatch')
        cur.execute('SELECT doc_key,title,access_level,source_url,source_hash FROM rag.documents ORDER BY doc_key')
        documents = []
        for key, title, level, url, source_hash in cur.fetchall():
            if level not in ('all', 'it'):
                raise ValueError('invalid_stored_permission')
            documents.append(dict(doc_key=key, access_level=level, source_hash=source_hash,
                                  attributes_hash=hashlib.sha256(json.dumps([title,url]).encode()).hexdigest(), chunks=[]))
        by_key = {d['doc_key']: d for d in documents}
        cur.execute('SELECT d.doc_key,c.chunk_no,c.section,c.content,c.content_hash,c.embedding_model,c.metadata,vector_dims(c.embedding),c.embedding::text FROM rag.documents d JOIN rag.chunks c ON c.document_id=d.id ORDER BY d.doc_key,c.chunk_no')
        for key, number, section, content, content_hash, model, metadata, dims, vector in cur.fetchall():
            if hashlib.sha256(content.encode()).hexdigest() != content_hash:
                raise ValueError('stored_content_hash_mismatch')
            if dims != 3072 or model != 'text-embedding-3-large':
                raise ValueError('stored_embedding_mismatch')
            by_key[key]['chunks'].append(dict(chunk_no=number, content_hash=content_hash,
                section_hash=hashlib.sha256(section.encode()).hexdigest(), embedding_model=model,
                dimensions=dims, metadata_hash=hashlib.sha256(json.dumps(metadata,sort_keys=True).encode()).hexdigest(),
                vector_hash=hashlib.sha256(vector.encode()).hexdigest(),
                chunking=metadata.get('chunking'), settings_hash=metadata.get('index_settings_hash')))
        for doc in documents:
            numbers = [c['chunk_no'] for c in doc['chunks']]
            if numbers != list(range(len(numbers))):
                raise ValueError('duplicate_or_missing_chunk_number')
            doc['chunk_count'] = len(numbers)
        return dict(mode='postgres', captured_at=datetime.now(timezone.utc).isoformat(),
                    vector_version=extension[0], documents=documents)


def compare(before, after):
    if before.get('mode') != 'postgres' or after.get('mode') != 'postgres':
        raise ValueError('postgres_records_required')
    a = {d['doc_key']:d for d in before['documents']}
    b = {d['doc_key']:d for d in after['documents']}
    added = sorted(b.keys()-a.keys()); removed = sorted(a.keys()-b.keys())
    changed = sorted(k for k in a.keys() & b.keys() if a[k] != b[k])
    return dict(same_inventory=not (added or removed or changed), added=added, removed=removed, changed=changed,
                actual_restart_observed=False)  # External restart evidence must be attached by lead.


def output_path(value):
    path = Path(value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError('output_outside_owner_directory')
    return path


def write_new(path, value):
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    fd = os.open(output_path(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        stream.write(payload)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    capture = sub.add_parser('snapshot')
    capture.add_argument('--allow-db', action='store_true')
    capture.add_argument('--output', required=True)
    comparison = sub.add_parser('compare')
    comparison.add_argument('--before', required=True); comparison.add_argument('--after', required=True)
    comparison.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        target = output_path(args.output)
        if target.exists():
            raise ValueError('output_already_exists')
        if args.command == 'snapshot':
            if not args.allow_db or not os.getenv('DATABASE_URL'):
                raise ValueError('db_execution_not_configured_or_authorized')
            import psycopg
            with psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=3,
                    options='-c default_transaction_read_only=on -c default_transaction_isolation=repeatable\\ read -c statement_timeout=10000') as db:
                result = snapshot(db)
        else:
            from rag_verify import load_unique_json
            result = compare(load_unique_json(Path(args.before)), load_unique_json(Path(args.after)))
        write_new(target, result)
        print(json.dumps({'ok':True, 'same_inventory':result.get('same_inventory')}))
        return 0 if result.get('same_inventory', True) else 1
    except Exception:
        print(json.dumps({'ok':False,'reason':'db_verification_failed'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
