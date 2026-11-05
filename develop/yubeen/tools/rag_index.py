"""P1-1 색인 공통 엔진. 외부 연결은 호출자가 제공하며 자체 네트워크 호출은 없다."""
import copy
import hashlib
import json
import math
import threading
from contextlib import contextmanager
from pathlib import Path

import rag_prepare as prepare

ROOT = Path(__file__).resolve().parents[1]


class IndexError(ValueError):
    """원문이나 외부 오류 대신 고정 오류 코드만 전달한다."""


def load_settings(path=None):
    settings = json.loads((path or ROOT / 'config/rag-settings.json').read_text())
    return validate_settings(settings)


def validate_settings(settings):
    required = {'embedding_model': 'text-embedding-3-large', 'embedding_dimensions': 3072,
                'distance': 'cosine', 'top_k': 3, 'chunking': 'section',
                'chunking_version': 'p0-2-v1', 'overlap': 0,
                'content_review_max_utf8_bytes': 8000, 'score_threshold': None}
    if any(settings.get(k) != v for k, v in required.items()):
        raise IndexError('invalid_settings')
    return settings


def settings_hash(settings):
    fields = ('embedding_model', 'embedding_dimensions', 'chunking', 'chunking_version',
              'overlap', 'content_review_max_utf8_bytes')
    return hashlib.sha256(json.dumps({k: settings[k] for k in fields}, sort_keys=True).encode()).hexdigest()


def validate_embedding(response, settings):
    if not isinstance(response, dict) or response.get('model') != settings['embedding_model']:
        raise IndexError('embedding_model_mismatch')
    vector = response.get('embedding')
    if not isinstance(vector, list) or len(vector) != settings['embedding_dimensions']:
        raise IndexError('embedding_dimension_mismatch')
    if any(isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) for n in vector):
        raise IndexError('embedding_invalid_value')
    if not any(vector):
        raise IndexError('embedding_zero_vector')
    return list(vector)


def document_matches(stored, document, chunks, settings):
    if stored is None:
        return False
    if any(stored.get(k) != document[k] for k in ('doc_key', 'title', 'access_level', 'source_url', 'source_hash')):
        return False
    old = stored.get('chunks', [])
    if len(old) != len(chunks):
        return False
    for left, right in zip(old, chunks):
        if any(left.get(k) != right[k] for k in ('chunk_no', 'content_hash')):
            return False
        if (left.get('embedding_model') != settings['embedding_model']
                or left.get('dimensions') != settings['embedding_dimensions']
                or left.get('metadata', {}).get('index_settings_hash') != settings_hash(settings)):
            return False
    return True


def version_token(document):
    """DB 기존 열과 청크 상태로 저장 직전 비교할 불투명 버전을 만든다."""
    if document is None:
        return None
    fields = ('id', 'doc_key', 'title', 'access_level', 'source_url', 'source_hash', 'updated_at')
    payload = {key: document.get(key) for key in fields}
    payload['chunks'] = [{key: chunk.get(key) for key in
        ('chunk_no', 'content_hash', 'embedding_model', 'metadata', 'dimensions')}
        for chunk in document.get('chunks', [])]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def confirmed_restricted_permission(snapshot, key):
    """명시 메타데이터만 신뢰한다. 중복·충돌·신원 불일치 본문의 권한은 추정하지 않는다."""
    entries = [item for item in snapshot['list_response']['docs'] if item['name'] == key]
    if len(entries) != 1:
        return False
    levels = []
    if 'access_level' in entries[0]:
        levels.append(entries[0]['access_level'])
    response = snapshot['document_responses'].get(key)
    if isinstance(response, dict) and response.get('name') == key and 'access_level' in response:
        levels.append(response['access_level'])
    return bool(levels) and all(level == 'it' for level in levels)


def index_snapshot(snapshot, embedder, store, settings=None):
    """모든 벡터 준비 후, 저장 트랜잭션 안에서 읽었던 버전과 비교해 교체한다."""
    settings = validate_settings(settings) if settings is not None else load_settings()
    if 'prepared_rows' in snapshot:
        raise IndexError('masked_snapshot_not_indexable')
    rows = prepare.inventory(snapshot)
    results = []
    for row in rows:
        result = {'document_ref': hashlib.sha256(row['doc_key'].encode()).hexdigest(),
                  'status': 'rejected', 'reason': None, 'chunk_count': 0}
        try:
            # 원본 오류가 있어도 신뢰 가능한 권한 축소를 먼저 처리한다.
            restricted = confirmed_restricted_permission(snapshot, row['doc_key'])
            if row['reasons'] and not restricted:
                result['reason'] = 'source_validation_failed'
                results.append(result)
                continue
            existing = store.read(row['doc_key'])
            if existing and existing['access_level'] == 'all' and restricted:
                try:
                    store.suspend(row['doc_key'])
                except IndexError:
                    raise
                except Exception:
                    raise IndexError('permission_suspension_failed') from None
                result['reason'] = 'permission_reduction_requires_review'
                results.append(result)
                continue
            if existing and not existing.get('chunks'):
                result['reason'] = 'index_suspended_requires_review'
                results.append(result)
                continue
            if row['reasons']:
                result['reason'] = 'source_validation_failed'
                results.append(result)
                continue
            doc = snapshot['document_responses'][row['doc_key']]
            document = {k: row[k] for k in ('doc_key', 'title', 'access_level', 'source_url', 'source_hash')}
            prepared = prepare.chunk_document(row['doc_key'], doc['title'], doc['text'], row['access_level'], settings['chunking'])
            if prepared['status'] != 'complete':
                result['reason'] = 'incomplete_chunks'
                results.append(result)
                continue
            chunks = prepared['chunks']
            if document_matches(existing, document, chunks, settings):
                result.update(status='skipped', chunk_count=len(chunks))
            else:
                ready = []
                for chunk in chunks:
                    payload = copy.deepcopy(chunk)
                    payload['embedding'] = validate_embedding(embedder(chunk['content'], settings['embedding_model'], settings['embedding_dimensions']), settings)
                    payload['embedding_model'] = settings['embedding_model']
                    payload['metadata']['index_settings_hash'] = settings_hash(settings)
                    ready.append(payload)
                store.replace(document, ready, expected_version=version_token(existing))
                result.update(status='indexed', chunk_count=len(ready))
        except IndexError as exc:
            known = {'stale_document_version', 'index_suspended_requires_review',
                     'storage_rollback_failed', 'storage_commit_unknown', 'storage_connection_unusable',
                     'permission_suspension_failed', 'storage_replace_failed', 'storage_read_failed'}
            result.update(status='failed', reason=str(exc) if str(exc) in known else 'index_unavailable')
        except Exception:
            result.update(status='failed', reason='index_unavailable')
        results.append(result)
    return {'mode': getattr(store, 'mode', 'unverified'), 'documents': results,
            'counts': {s: sum(r['status'] == s for r in results) for s in ('indexed', 'skipped', 'rejected', 'failed')}}


class MockStore:
    """테스트 전용 저장 더블이다. PostgreSQL 대체 운영 저장소가 아니다."""
    mode = 'mock'

    def __init__(self):
        self.documents = {}
        self.next_id = 1
        self.fail_after_delete = False
        self.replacements = 0
        self.suspended = set()
        self.lock = threading.RLock()

    def read(self, key):
        with self.lock:
            return copy.deepcopy(self.documents.get(key))

    def suspend(self, key):
        with self.lock:
            if key in self.documents:
                self.suspended.add(key)
                self.documents[key]['chunks'] = []
                self.documents[key]['access_level'] = 'it'
                self.documents[key]['updated_at'] = prepare.now()

    def replace(self, document, chunks, expected_version=None):
        with self.lock:
            current = self.documents.get(document['doc_key'])
            if version_token(current) != expected_version:
                raise IndexError('stale_document_version')
            if current and not current.get('chunks'):
                raise IndexError('index_suspended_requires_review')
            previous = copy.deepcopy(self.documents)
            old_id = current['id'] if current else None
            try:
                self.documents.pop(document['doc_key'], None)
                if self.fail_after_delete:
                    raise IndexError('mock_storage_failure')
                item = dict(document, id=old_id or self.next_id, updated_at=prepare.now())
                item['chunks'] = [dict(copy.deepcopy(c), document_id=item['id'], dimensions=len(c['embedding'])) for c in chunks]
                if len({c['chunk_no'] for c in chunks}) != len(chunks):
                    raise IndexError('duplicate_chunk_number')
                self.documents[document['doc_key']] = item
                if old_id is None:
                    self.next_id += 1
                self.replacements += 1
            except Exception:
                self.documents = previous
                raise


class PostgresStore:
    """소유권을 넘겨받은 전용 연결만 사용한다. 실패 연결은 풀에 반환하지 않고 닫는다."""
    mode = 'postgres_unverified'

    def __init__(self, connection):
        if getattr(connection, 'autocommit', True):
            raise IndexError('transaction_required')
        self.connection = connection
        self.usable = True

    def _discard(self):
        self.usable = False
        try:
            self.connection.close()
        except Exception:
            pass

    @contextmanager
    def _transaction(self, error_code):
        if not self.usable:
            raise IndexError('storage_connection_unusable')
        try:
            with self.connection.cursor() as cursor:
                yield cursor
        except Exception as original:
            try:
                self.connection.rollback()
            except Exception:
                self._discard()
                raise IndexError('storage_rollback_failed') from None
            disconnected = getattr(original, 'sqlstate', '') or ''
            closed = getattr(self.connection, 'closed', False)
            if (isinstance(closed, (bool, int)) and bool(closed)) or str(disconnected).startswith('08'):
                self._discard()
                raise IndexError('storage_connection_unusable') from None
            if isinstance(original, IndexError):
                raise original from None
            raise IndexError(error_code) from None
        else:
            try:
                self.connection.commit()
            except Exception:
                # 커밋 ACK 유실 여부를 알 수 없으므로 보존/실패를 단정하거나 재사용하지 않는다.
                self._discard()
                raise IndexError('storage_commit_unknown') from None

    def _read(self, cursor, key, lock=False):
        suffix = ' FOR UPDATE' if lock else ''
        cursor.execute('SELECT id,doc_key,title,access_level,source_url,source_hash,updated_at FROM rag.documents WHERE doc_key=%s' + suffix, (key,))
        row = cursor.fetchone()
        if row is None:
            return None
        result = dict(zip(('id', 'doc_key', 'title', 'access_level', 'source_url', 'source_hash', 'updated_at'), row))
        cursor.execute('SELECT chunk_no,content_hash,embedding_model,metadata,vector_dims(embedding) FROM rag.chunks WHERE document_id=%s ORDER BY chunk_no', (result['id'],))
        result['chunks'] = [dict(zip(('chunk_no', 'content_hash', 'embedding_model', 'metadata', 'dimensions'), c)) for c in cursor.fetchall()]
        return result

    def _lock(self, cursor, key):
        # 신규 문서도 직렬화한다. 이 어댑터를 사용하는 모든 쓰기 경로가 같은 잠금 키를 쓴다.
        cursor.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))', ('oke-rag:' + key,))

    def read(self, key):
        with self._transaction('storage_read_failed') as cursor:
            result = self._read(cursor, key)
        return result

    def suspend(self, key):
        with self._transaction('permission_suspension_failed') as cursor:
            self._lock(cursor, key)
            cursor.execute('SELECT id FROM rag.documents WHERE doc_key=%s FOR UPDATE', (key,))
            row = cursor.fetchone()
            if row is not None:
                cursor.execute('UPDATE rag.documents SET access_level=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s', ('it', row[0]))
                cursor.execute('DELETE FROM rag.chunks WHERE document_id=%s', (row[0],))

    def replace(self, document, chunks, expected_version=None):
        with self._transaction('storage_replace_failed') as cursor:
            self._lock(cursor, document['doc_key'])
            current = self._read(cursor, document['doc_key'], lock=True)
            if version_token(current) != expected_version:
                raise IndexError('stale_document_version')
            if current and not current.get('chunks'):
                raise IndexError('index_suspended_requires_review')
            if current is None:
                # 같은 잠금 규약을 안 쓰는 외부 INSERT에도 기존 행을 덮어쓰지 않는다.
                cursor.execute('INSERT INTO rag.documents (doc_key,title,access_level,source_url,source_hash,updated_at) VALUES (%s,%s,%s,%s,%s,CURRENT_TIMESTAMP) ON CONFLICT (doc_key) DO NOTHING RETURNING id', tuple(document[k] for k in ('doc_key', 'title', 'access_level', 'source_url', 'source_hash')))
                inserted = cursor.fetchone()
                if inserted is None:
                    raise IndexError('stale_document_version')
                document_id = inserted[0]
            else:
                document_id = current['id']
                cursor.execute('UPDATE rag.documents SET title=%s,access_level=%s,source_url=%s,source_hash=%s,updated_at=CURRENT_TIMESTAMP WHERE id=%s', tuple(document[k] for k in ('title', 'access_level', 'source_url', 'source_hash')) + (document_id,))
            cursor.execute('DELETE FROM rag.chunks WHERE document_id=%s', (document_id,))
            for chunk in chunks:
                vector = '[' + ','.join(str(n) for n in chunk['embedding']) + ']'
                cursor.execute('INSERT INTO rag.chunks (document_id,chunk_no,section,content,content_hash,embedding,embedding_model,metadata) VALUES (%s,%s,%s,%s,%s,%s::vector,%s,%s::jsonb)',
                    (document_id, chunk['chunk_no'], chunk['section'], chunk['content'], chunk['content_hash'], vector, chunk['embedding_model'], json.dumps(chunk['metadata'], ensure_ascii=False)))
