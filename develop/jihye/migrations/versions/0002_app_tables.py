"""Create the seven business tables and dedicated ticket-number sequence."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateSequence, DropSequence

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def pk():
    return sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False)


def created():
    return sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)


def upgrade():
    op.execute(CreateSequence(sa.Sequence("ticket_number_seq", start=2001, schema="app", data_type=sa.BigInteger())))
    op.create_table("employees", pk(), sa.Column("name", sa.Text(), nullable=False),
        sa.Column("dept", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employees")),
        sa.UniqueConstraint("name", name=op.f("uq_employees_name")), schema="app")
    op.create_table("users", pk(),
        sa.Column("employee_id", sa.BigInteger(), nullable=False),
        sa.Column("login_id", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False), sa.Column("role", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), server_default=sa.text("true"), nullable=False), created(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.ForeignKeyConstraint(["employee_id"], ["app.employees.id"], name=op.f("fk_users_employee_id_employees")),
        sa.UniqueConstraint("employee_id", name=op.f("uq_users_employee_id")),
        sa.UniqueConstraint("login_id", name=op.f("uq_users_login_id")),
        sa.CheckConstraint("role IN ('employee','admin')", name=op.f("ck_users_role")), schema="app")
    op.create_table("sessions", pk(), sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
        sa.ForeignKeyConstraint(["user_id"], ["app.users.id"], name=op.f("fk_sessions_user_id_users")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_sessions_token_hash")), schema="app")
    op.create_table("inquiries", pk(), sa.Column("request_id", sa.Text(), nullable=False),
        sa.Column("requester_id", sa.BigInteger(), nullable=False), sa.Column("question", sa.Text(), nullable=False),
        sa.Column("attempt", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("context", sa.Text(), nullable=True), sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False), created(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_inquiries")),
        sa.ForeignKeyConstraint(["requester_id"], ["app.employees.id"], name=op.f("fk_inquiries_requester_id_employees")),
        sa.UniqueConstraint("request_id", name=op.f("uq_inquiries_request_id")),
        sa.CheckConstraint("char_length(request_id) BETWEEN 1 AND 64", name=op.f("ck_inquiries_request_id_length")),
        sa.CheckConstraint("char_length(question) BETWEEN 1 AND 500", name=op.f("ck_inquiries_question_length")),
        sa.CheckConstraint("attempt >= 1", name=op.f("ck_inquiries_attempt")), schema="app")
    op.create_table("tickets", pk(),
        sa.Column("ticket_id", sa.Text(), server_default=sa.text("'T-' || nextval('app.ticket_number_seq'::regclass)::text"), nullable=False),
        sa.Column("request_key", sa.Text(), nullable=False), sa.Column("inquiry_id", sa.BigInteger(), nullable=True),
        sa.Column("requester_id", sa.BigInteger(), nullable=False), sa.Column("title", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False), sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'open'"), nullable=False),
        sa.Column("assignee_id", sa.BigInteger(), nullable=True), sa.Column("reply", sa.Text(), nullable=True),
        created(), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tickets")),
        sa.ForeignKeyConstraint(["inquiry_id"], ["app.inquiries.id"], name=op.f("fk_tickets_inquiry_id_inquiries")),
        sa.ForeignKeyConstraint(["requester_id"], ["app.employees.id"], name=op.f("fk_tickets_requester_id_employees")),
        sa.ForeignKeyConstraint(["assignee_id"], ["app.employees.id"], name=op.f("fk_tickets_assignee_id_employees")),
        sa.UniqueConstraint("request_key", name=op.f("uq_tickets_request_key")),
        sa.UniqueConstraint("ticket_id", name=op.f("uq_tickets_ticket_id")),
        sa.CheckConstraint("char_length(request_key) BETWEEN 1 AND 64", name=op.f("ck_tickets_request_key_length")),
        sa.CheckConstraint("priority IN ('normal','high')", name=op.f("ck_tickets_priority")),
        sa.CheckConstraint("status IN ('open','in_progress','resolved')", name=op.f("ck_tickets_status")), schema="app")
    op.create_table("alerts", pk(), sa.Column("ticket_id", sa.BigInteger(), nullable=True),
        sa.Column("event_key", sa.Text(), nullable=True), sa.Column("workflow", sa.Text(), nullable=False),
        sa.Column("node", sa.Text(), nullable=False), sa.Column("message", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False), created(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
        sa.ForeignKeyConstraint(["ticket_id"], ["app.tickets.id"], name=op.f("fk_alerts_ticket_id_tickets")),
        sa.UniqueConstraint("event_key", name=op.f("uq_alerts_event_key")), schema="app")
    op.create_table("dlq", pk(), sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("execution_ref", sa.Text(), nullable=True), sa.Column("workflow", sa.Text(), nullable=False),
        sa.Column("node", sa.Text(), nullable=False), sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("safe_payload", postgresql.JSONB(), nullable=False), sa.Column("status", sa.Text(), nullable=False), created(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dlq")), schema="app")
    for table, columns in (
        ("sessions", ["user_id"]), ("sessions", ["expires_at"]),
        ("inquiries", ["requester_id", "created_at"]),
        ("tickets", ["inquiry_id"]), ("tickets", ["requester_id"]),
        ("tickets", ["assignee_id"]), ("tickets", ["status", "created_at"]),
        ("alerts", ["ticket_id"]), ("alerts", ["created_at"]),
        ("dlq", ["request_id"]), ("dlq", ["execution_ref"]),
    ):
        op.create_index(f"ix_{table}_{'_'.join(columns)}", table, columns, schema="app")


def downgrade():
    for table in ("dlq", "alerts", "tickets", "inquiries", "sessions", "users", "employees"):
        op.drop_table(table, schema="app")
    op.execute(DropSequence(sa.Sequence("ticket_number_seq", schema="app")))
