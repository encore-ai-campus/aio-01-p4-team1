"""Create RAG documents and 3072-dimensional chunks."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("documents",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("doc_key", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("access_level", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("source_hash", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        sa.UniqueConstraint("doc_key", name=op.f("uq_documents_doc_key")),
        sa.CheckConstraint("access_level IN ('all','it')", name=op.f("ck_documents_access_level")),
        schema="rag")
    op.create_table("chunks",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("chunk_no", sa.Integer(), nullable=False),
        sa.Column("section", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(3072), nullable=False),
        sa.Column("embedding_model", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chunks")),
        sa.ForeignKeyConstraint(["document_id"], ["rag.documents.id"], name=op.f("fk_chunks_document_id_documents")),
        sa.UniqueConstraint("document_id", "chunk_no", name=op.f("uq_chunks_document_id")),
        sa.CheckConstraint("chunk_no >= 0", name=op.f("ck_chunks_chunk_no")),
        schema="rag")


def downgrade():
    op.drop_table("chunks", schema="rag")
    op.drop_table("documents", schema="rag")
