"""Contract and real PostgreSQL constraints, using rollback-only synthetic records."""

import os
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import BigInteger, DateTime, inspect, select, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError

from app.db.base import Base, include_migration_name
from app.db.models import Alert, Dlq, Employee, Inquiry, Session, Ticket, User
from app.db.session import create_db_engine

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("OKE_RUN_DB_TESTS") != "1" or not os.environ.get("DATABASE_URL"),
    reason="requires the isolated Compose database and explicit opt-in",
)]

NULLABLE = {
    "employees": set(), "users": set(), "sessions": {"revoked_at"},
    "inquiries": {"context", "result"}, "tickets": {"inquiry_id", "assignee_id", "reply"},
    "alerts": {"ticket_id", "event_key"}, "dlq": {"request_id", "execution_ref"},
}
FIELDS = {
    "employees": "id name dept",
    "users": "id employee_id login_id password_hash role is_active must_change_password created_at",
    "sessions": "id user_id token_hash expires_at revoked_at",
    "inquiries": "id request_id requester_id question attempt context result status created_at",
    "tickets": "id ticket_id request_key inquiry_id requester_id title category priority status assignee_id reply created_at updated_at",
    "alerts": "id ticket_id event_key workflow node message severity created_at",
    "dlq": "id request_id execution_ref workflow node reason safe_payload status created_at",
}


@pytest.fixture
def engine():
    instance = create_db_engine()
    yield instance
    instance.dispose()


@pytest.fixture
def db(engine):
    with engine.connect() as connection:
        transaction = connection.begin()
        yield connection
        transaction.rollback()


def add(db, model, **values):
    return db.execute(model.__table__.insert().values(**values).returning(model.id)).scalar_one()


def employee(db):
    return add(db, Employee, name=f"p04-fixture-{uuid4().hex}", dept="검증용 부서")


def account(db, employee_id):
    return add(db, User, employee_id=employee_id, login_id=uuid4().hex,
               password_hash=secrets.token_hex(32), role="employee")


def ticket_values(requester_id):
    return dict(request_key=uuid4().hex, requester_id=requester_id,
                title="합성 시험 문의", category="fixture", priority="normal")


def test_extension_schema_revision_and_rag_tables(engine):
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT extversion FROM pg_extension WHERE extname='vector'"))
        assert connection.scalar(text("SELECT version_num FROM public.alembic_version")) == "0005"
        inspector = inspect(connection)
        assert set(inspector.get_table_names(schema="app")) == set(FIELDS)
        assert set(inspector.get_table_names(schema="rag")) == {"documents", "chunks"}


@pytest.mark.parametrize("table", FIELDS)
def test_physical_columns_identity_null_and_time_types(engine, table):
    inspector = inspect(engine)
    columns = {column["name"]: column for column in inspector.get_columns(table, schema="app")}
    assert set(columns) == set(FIELDS[table].split())
    assert {name for name, column in columns.items() if column["nullable"]} == NULLABLE[table]
    assert isinstance(columns["id"]["type"], BigInteger)
    assert columns["id"].get("identity")
    for name in {"created_at", "updated_at", "expires_at", "revoked_at"} & columns.keys():
        assert isinstance(columns[name]["type"], DateTime) and columns[name]["type"].timezone
    for name in {"result", "safe_payload"} & columns.keys():
        assert isinstance(columns[name]["type"], JSONB)


def test_foreign_keys_and_indexes_cover_contract(engine):
    inspector = inspect(engine)
    expected = {
        ("users", "employee_id"): "employees", ("sessions", "user_id"): "users",
        ("inquiries", "requester_id"): "employees", ("tickets", "inquiry_id"): "inquiries",
        ("tickets", "requester_id"): "employees", ("tickets", "assignee_id"): "employees",
        ("alerts", "ticket_id"): "tickets",
    }
    actual = {}
    for table in FIELDS:
        indexes = inspector.get_indexes(table, schema="app")
        for fk in inspector.get_foreign_keys(table, schema="app"):
            assert fk["referred_schema"] == "app" and fk["referred_columns"] == ["id"]
            assert fk["options"].get("ondelete") in {None, "NO ACTION"}
            column = fk["constrained_columns"][0]
            actual[table, column] = fk["referred_table"]
            assert any(index["column_names"][0] == column for index in indexes)
    assert actual == expected


def test_unique_constraints_match_contract(engine):
    expected = {
        "employees": {("name",)}, "users": {("employee_id",), ("login_id",)},
        "sessions": {("token_hash",)}, "inquiries": {("request_id",)},
        "tickets": {("ticket_id",), ("request_key",)}, "alerts": {("event_key",)}, "dlq": set(),
    }
    inspector = inspect(engine)
    for table, unique in expected.items():
        assert {tuple(item["column_names"]) for item in inspector.get_unique_constraints(table, schema="app")} == unique


def test_orm_and_migrated_schema_agree(engine):
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={
            "include_schemas": True, "include_name": include_migration_name,
            "compare_type": True, "compare_server_default": False,
        })
        # Don't evaluate a volatile nextval default during schema comparison.
        assert compare_metadata(context, Base.metadata) == []


def test_defaults_nullable_fields_and_jsonb_roundtrip(db):
    owner = employee(db)
    user = account(db, owner)
    user_row = db.execute(select(User.__table__).where(User.id == user)).mappings().one()
    assert user_row["is_active"] is True and user_row["must_change_password"] is True
    assert user_row["created_at"].tzinfo
    session = add(db, Session, user_id=user, token_hash=secrets.token_hex(32),
                  expires_at=datetime.now(timezone.utc) + timedelta(hours=8))
    assert db.scalar(select(Session.revoked_at).where(Session.id == session)) is None
    inquiry = add(db, Inquiry, request_id=uuid4().hex, requester_id=owner, question="합성 문의", status="fixture-state")
    row = db.execute(select(Inquiry.__table__).where(Inquiry.id == inquiry)).mappings().one()
    assert row["attempt"] == 1 and row["context"] is None and row["result"] is None
    result = {"fixture": True, "nested": {"items": [1, "합성"]}}
    db.execute(Inquiry.__table__.update().where(Inquiry.id == inquiry).values(result=result))
    assert db.scalar(select(Inquiry.result).where(Inquiry.id == inquiry)) == result
    ticket = add(db, Ticket, **ticket_values(owner))
    record = db.execute(select(Ticket.__table__).where(Ticket.id == ticket)).mappings().one()
    assert record["status"] == "open" and record["inquiry_id"] is None
    assert record["assignee_id"] is None and record["reply"] is None
    assert record["created_at"].tzinfo and record["updated_at"].tzinfo
    alert_fields = dict(workflow="fixture", node="fixture", message="합성 안내", severity="fixture")
    add(db, Alert, **alert_fields)
    add(db, Alert, **alert_fields)  # NULL unique keys don't deduplicate unrelated alerts.
    dlq = add(db, Dlq, workflow="fixture", node="fixture", reason="fixture", status="fixture-state", safe_payload={"stage": "test"})
    dlq_row = db.execute(select(Dlq.__table__).where(Dlq.id == dlq)).mappings().one()
    assert dlq_row["request_id"] is None and dlq_row["execution_ref"] is None
    assert dlq_row["safe_payload"] == {"stage": "test"}


@pytest.mark.parametrize("case", ["employee_name", "employee_account", "login_id", "token_hash",
                                   "request_id", "request_key", "ticket_id", "event_key"])
def test_duplicate_keys_are_rejected_by_postgresql(db, case):
    owner = employee(db)
    user = account(db, owner)
    if case == "employee_name":
        model = Employee
        values = dict(name=db.scalar(select(Employee.name).where(Employee.id == owner)), dept="검증용 부서")
    elif case in {"employee_account", "login_id"}:
        model = User
        values = dict(employee_id=owner if case == "employee_account" else employee(db),
                      login_id=uuid4().hex if case == "employee_account" else db.scalar(select(User.login_id).where(User.id == user)),
                      password_hash=secrets.token_hex(32), role="employee")
    elif case == "token_hash":
        model = Session
        values = dict(user_id=user, token_hash=secrets.token_hex(32), expires_at=datetime.now(timezone.utc))
        add(db, model, **values)
    elif case == "request_id":
        model = Inquiry
        values = dict(request_id=uuid4().hex, requester_id=owner, question="합성 문의", status="fixture")
        add(db, model, **values)
    elif case in {"request_key", "ticket_id"}:
        model = Ticket
        original = ticket_values(owner)
        first = add(db, model, **original)
        values = original if case == "request_key" else {
            **ticket_values(owner), "ticket_id": db.scalar(select(Ticket.ticket_id).where(Ticket.id == first))}
    else:
        model = Alert
        values = dict(event_key=uuid4().hex, workflow="fixture", node="fixture", message="合成", severity="fixture")
        add(db, model, **values)
    with pytest.raises(IntegrityError) as caught:
        with db.begin_nested():
            add(db, model, **values)
    assert caught.value.orig.sqlstate == "23505"


@pytest.mark.parametrize("model,field,value", [
    (Inquiry, "request_id", ""), (Inquiry, "request_id", "x" * 65),
    (Inquiry, "question", ""), (Inquiry, "question", "가" * 501), (Inquiry, "attempt", 0),
    (User, "role", "superuser"), (Ticket, "priority", "urgent"), (Ticket, "status", "접수"),
    (Ticket, "request_key", ""), (Ticket, "request_key", "x" * 65),
])
def test_invalid_business_values_are_rejected(db, model, field, value):
    owner = employee(db)
    if model is Inquiry:
        values = dict(request_id=uuid4().hex, requester_id=owner, question="합성 문의", status="fixture")
    elif model is User:
        values = dict(employee_id=owner, login_id=uuid4().hex, password_hash=secrets.token_hex(32), role="employee")
    else:
        values = ticket_values(owner)
    with pytest.raises(IntegrityError) as caught:
        with db.begin_nested():
            add(db, model, **{**values, field: value})
    assert caught.value.orig.sqlstate == "23514"


@pytest.mark.parametrize("model,field", [(User, "employee_id"), (Session, "user_id"),
    (Inquiry, "requester_id"), (Ticket, "inquiry_id"), (Ticket, "requester_id"),
    (Ticket, "assignee_id"), (Alert, "ticket_id")])
def test_missing_foreign_keys_are_rejected(db, model, field):
    owner = employee(db)
    if model is User:
        values = dict(employee_id=owner, login_id=uuid4().hex, password_hash=secrets.token_hex(32), role="employee")
    elif model is Session:
        values = dict(user_id=account(db, owner), token_hash=secrets.token_hex(32), expires_at=datetime.now(timezone.utc))
    elif model is Inquiry:
        values = dict(request_id=uuid4().hex, requester_id=owner, question="합성 문의", status="fixture")
    elif model is Ticket:
        values = ticket_values(owner)
    else:
        values = dict(workflow="fixture", node="fixture", message="합성 안내", severity="fixture")
    with pytest.raises(IntegrityError) as caught:
        with db.begin_nested():
            add(db, model, **{**values, field: 9223372036854770000})
    assert caught.value.orig.sqlstate == "23503"


def test_ticket_number_sequence_starts_at_2001_and_is_separate_from_pk(db):
    start = db.scalar(text("SELECT start_value FROM pg_sequences WHERE schemaname='app' AND sequencename='ticket_number_seq'"))
    assert start == 2001
    pristine = not db.scalar(text("SELECT is_called FROM app.ticket_number_seq"))
    owner = employee(db)
    first = add(db, Ticket, id=900000, **ticket_values(owner))
    second = add(db, Ticket, **ticket_values(owner))
    a = int(db.scalar(select(Ticket.ticket_id).where(Ticket.id == first))[2:])
    b = int(db.scalar(select(Ticket.ticket_id).where(Ticket.id == second))[2:])
    assert a >= 2001 and b == a + 1 and a != first
    if pristine:
        assert a == 2001
    # Sequence gaps from rollback are expected; never reset/reuse display numbers.


def test_no_seed_records_left_behind(engine):
    with engine.connect() as connection:
        for table in FIELDS:
            assert connection.scalar(text(f'SELECT count(*) FROM app."{table}"')) == 0


def test_upgrade_head_again_does_not_change_schema_or_rows(engine):
    def snapshot():
        with engine.connect() as connection:
            objects = connection.execute(text("SELECT c.oid,c.relname,c.relkind FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('app','rag') ORDER BY c.oid")).all()
            rows = tuple(connection.scalar(text(f'SELECT count(*) FROM app."{table}"')) for table in FIELDS)
            sequence = connection.execute(text("SELECT last_value,is_called FROM app.ticket_number_seq")).one()
            return objects, rows, sequence
    before = snapshot()
    command.upgrade(Config("migrations/alembic.ini"), "head")
    assert snapshot() == before
