"""Real pgvector storage and permission-filtered exact cosine retrieval."""

import os
from uuid import uuid4

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import DataError, IntegrityError

from app.db.models import Chunk, Document
from app.db.session import create_db_engine

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("OKE_RUN_DB_TESTS") != "1" or not os.environ.get("DATABASE_URL"),
    reason="requires the isolated Compose DB",
)]


def test_shape_and_access_rejection():
    engine = create_db_engine()
    try:
        inspector = inspect(engine)
        cols = {item["name"]: item for item in inspector.get_columns("chunks", schema="rag")}
        assert set(cols) == {"id", "document_id", "chunk_no", "section", "content", "content_hash", "embedding", "embedding_model", "metadata"}
        assert "3072" in str(cols["embedding"]["type"])
        assert {"documents", "chunks"} == set(inspector.get_table_names(schema="rag"))
        with engine.begin() as db:
            with pytest.raises(IntegrityError):
                with db.begin_nested():
                    db.execute(Document.__table__.insert().values(
                        doc_key=f"fixture-{uuid4().hex}", title="합성", access_level="unknown", source_hash="hash"))
    finally:
        engine.dispose()


def test_dimension_zero_based_chunk_and_filtered_exact_cosine():
    engine = create_db_engine()
    try:
        with engine.connect() as db:
            tx = db.begin()
            try:
                docs = []
                for level in ("all", "it"):
                    docs.append(db.execute(Document.__table__.insert().values(
                        doc_key=f"fixture-{uuid4().hex}", title="합성", access_level=level,
                        source_hash="hash", source_url=None).returning(Document.id)).scalar_one())
                vector = [1.0] + [0.0] * 3071
                for number, doc_id in enumerate(docs):
                    db.execute(Chunk.__table__.insert().values(document_id=doc_id, chunk_no=0,
                        section="합성 절", content="합성 내용", content_hash=f"hash-{number}",
                        embedding=vector, embedding_model="text-embedding-3-large",
                        metadata={"source_range": [0, 3], "chunking_version": "p0-2-v1"}))
                with pytest.raises((DataError, IntegrityError)):
                    with db.begin_nested():
                        db.execute(Chunk.__table__.insert().values(document_id=docs[0], chunk_no=1,
                            section="합성", content="합성", content_hash="bad", embedding=[1.0] * 3071,
                            embedding_model="text-embedding-3-large", metadata={}))
                distance = Chunk.embedding.cosine_distance(vector)
                base = select(Document.access_level, (1 - distance).label("score")).join(
                    Chunk, Chunk.document_id == Document.id)
                assert [row.access_level for row in db.execute(base.where(
                    Document.id.in_(docs), Document.access_level.in_(["all"])).order_by(distance).limit(3))] == ["all"]
                rows = db.execute(base.where(Document.id.in_(docs), Document.access_level.in_(["all", "it"])).order_by(distance).limit(3)).all()
                assert {row.access_level for row in rows} == {"all", "it"}
                assert all(row.score == pytest.approx(1.0) for row in rows)
            finally:
                tx.rollback()
    finally:
        engine.dispose()
