"""Enable pgvector and create the application schemas; no records are seeded."""

from alembic import op
from sqlalchemy.schema import CreateSchema, DropSchema

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION vector")
    op.execute(CreateSchema("app"))
    op.execute(CreateSchema("rag"))


def downgrade():
    # No CASCADE: refuse to remove schemas/extension still used by other objects.
    op.execute(DropSchema("rag"))
    op.execute(DropSchema("app"))
    op.execute("DROP EXTENSION vector")
