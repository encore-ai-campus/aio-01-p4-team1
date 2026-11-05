"""RAG storage metadata; ingestion and access filtering belong to the RAG service."""

from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._types import PrimaryKey


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("access_level IN ('all','it')", name="access_level"),
        Index("ix_documents_access_level", "access_level"),
        {"schema": "rag"},
    )

    id: Mapped[PrimaryKey]
    doc_key: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(Text)
    access_level: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_hash: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_no"),
        CheckConstraint("chunk_no >= 0", name="chunk_no"),
        Index("ix_chunks_document_id", "document_id"),
        {"schema": "rag"},
    )

    id: Mapped[PrimaryKey]
    document_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rag.documents.id"))
    chunk_no: Mapped[int] = mapped_column(Integer)
    section: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(3072))
    embedding_model: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB)
