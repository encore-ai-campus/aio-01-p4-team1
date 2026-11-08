"""Add RAG lookup indexes and scoped, passwordless privilege roles."""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"], schema="rag")
    op.create_index("ix_documents_access_level", "documents", ["access_level"], schema="rag")
    for role in ("oke_app", "oke_rag_index", "oke_rag_search"):
        op.execute(f"DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{role}') THEN CREATE ROLE {role} NOLOGIN; END IF; END $$")
    for schema in ("app", "rag"):
        op.execute(f"REVOKE ALL ON SCHEMA {schema} FROM PUBLIC")
        op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA {schema} FROM PUBLIC")
        op.execute(f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA {schema} FROM PUBLIC")
        op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} REVOKE ALL ON TABLES FROM PUBLIC")
        op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} REVOKE ALL ON SEQUENCES FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA app TO oke_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO oke_app")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA app TO oke_app")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO oke_app")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT USAGE, SELECT ON SEQUENCES TO oke_app")
    op.execute("GRANT USAGE ON SCHEMA rag TO oke_rag_index, oke_rag_search")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA rag TO oke_rag_index")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA rag TO oke_rag_index")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA rag TO oke_rag_search")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA rag GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO oke_rag_index")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA rag GRANT USAGE, SELECT ON SEQUENCES TO oke_rag_index")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA rag GRANT SELECT ON TABLES TO oke_rag_search")


def downgrade():
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA rag REVOKE SELECT ON TABLES FROM oke_rag_search")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA rag REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM oke_rag_index")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA rag REVOKE USAGE, SELECT ON SEQUENCES FROM oke_rag_index")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM oke_app")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE USAGE, SELECT ON SEQUENCES FROM oke_app")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA rag FROM oke_rag_index, oke_rag_search")
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA rag FROM oke_rag_index")
    op.execute("REVOKE ALL ON SCHEMA rag FROM oke_rag_index, oke_rag_search")
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA app FROM oke_app")
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA app FROM oke_app")
    op.execute("REVOKE ALL ON SCHEMA app FROM oke_app")
    op.drop_index("ix_documents_access_level", table_name="documents", schema="rag")
    op.drop_index("ix_chunks_document_id", table_name="chunks", schema="rag")
    # Cluster roles may be shared by another DB; never drop them in a downgrade.
