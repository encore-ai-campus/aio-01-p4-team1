"""Permit application readiness to read migration bookkeeping only."""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("GRANT SELECT ON public.alembic_version TO oke_app")


def downgrade():
    op.execute("REVOKE SELECT ON public.alembic_version FROM oke_app")
