"""C03 adapter boundary. No driver, connection factory, credentials or HTTP calls.

Caller owns authentication/input validation and the supplied DB connection.
Only public access is supported until the C03 employee trust contract is settled.
"""
import math
from rag_index import load_settings, validate_embedding

# Contract-based draft: verify schema and exact-search plan after P0-5.
# MATERIALIZED prevents ranking an unrestricted candidate set.
SEARCH_SQL = """
WITH allowed AS MATERIALIZED (
 SELECT d.doc_key, c.chunk_no, c.section, c.content, c.embedding
 FROM rag.documents d JOIN rag.chunks c ON c.document_id = d.id
 WHERE d.access_level = ANY(%s) AND c.embedding_model = %s
)
SELECT doc_key, section, content, 1 - (embedding <=> %s::vector) AS score
FROM allowed
ORDER BY embedding <=> %s::vector ASC, doc_key ASC, chunk_no ASC
LIMIT %s
"""


def unavailable():
    return 503, {'ok': False, 'evidence': [], 'reason': 'search_unavailable'}


def valid_query(query):
    return isinstance(query, str) and bool(query.strip())


def validate_evidence(rows):
    """Repository protocol: list/tuple of dictionaries; project public C03 fields.

    No new score range policy: require finite numeric values, not probabilities.
    """
    if not isinstance(rows, (list, tuple)) or len(rows) > 3:
        raise ValueError('invalid_evidence_collection')
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('invalid_evidence')
        if not all(isinstance(row.get(k), str) and row[k].strip() for k in ('doc', 'section', 'text')):
            raise ValueError('invalid_evidence')
        score = row.get('score')
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
            raise ValueError('invalid_score')
        result.append({k: row[k] for k in ('doc', 'section', 'text', 'score')})
    return result


class PgvectorSearchAdapter:
    """Uses a caller-owned dedicated DB-API connection; does not commit/close it.

    Transaction lifetime, timeout and cleanup remain caller responsibilities.
    """
    def __init__(self, connection):
        self.connection = connection

    def search(self, vector, access_levels, settings):
        if access_levels != ['all']:
            raise ValueError('unverified_access')
        vector = validate_embedding({'model': settings['embedding_model'], 'embedding': vector}, settings)
        literal = '[' + ','.join(str(v) for v in vector) + ']'
        cursor = self.connection.cursor()
        try:
            cursor.execute(SEARCH_SQL, (['all'], settings['embedding_model'], literal, literal, 3))
            rows = cursor.fetchall()
        finally:
            cursor.close()
        if not isinstance(rows, (list, tuple)) or len(rows) > 3:
            raise ValueError('invalid_result_count')
        return validate_evidence([
            dict(zip(('doc', 'section', 'text', 'score'), row, strict=True))
            for row in rows
        ])


def search_with_adapters(query, access_levels, top_k, embedder, repository):
    """Provider protocol reuses Index: (text, model, dimensions)->{model,embedding}.

    Test with injected fakes; no fallback and no employee privilege inference.
    """
    if access_levels != ['all'] or type(top_k) is not int or top_k != 3:
        return unavailable()  # Internal boundary failure, not final input/auth HTTP policy.
    if not valid_query(query):
        return unavailable()
    try:
        settings = load_settings()
        vector = validate_embedding(embedder(query, settings['embedding_model'], settings['embedding_dimensions']), settings)
        evidence = validate_evidence(repository.search(vector, ['all'], settings))
        return 200, {'ok': True, 'evidence': evidence, 'reason': None if evidence else 'no_evidence'}
    except Exception:
        return unavailable()


def dispatch(query, access_levels, top_k=3, *, mode=None, adapter_enabled=False,
             embedder=None, repository=None, mock_search=None):
    """Mode is server-owned configuration, never a request field.

    Mock is available only when explicitly selected and provided by the caller.
    Adapter mode is disabled by default. This module creates no live clients.
    """
    if access_levels != ['all'] or type(top_k) is not int or top_k != 3:
        return unavailable()
    if not valid_query(query):
        return unavailable()
    if mode == 'mock' and mock_search is not None:
        try:
            return mock_search(query, access_levels, top_k)
        except Exception:
            return unavailable()
    if mode == 'adapter' and adapter_enabled and embedder is not None and repository is not None:
        return search_with_adapters(query, access_levels, top_k, embedder, repository)
    return unavailable()
