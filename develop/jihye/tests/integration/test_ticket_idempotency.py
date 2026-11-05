"""C05 PostgreSQL transactions and ACKs against the isolated Compose DB only."""

import os
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.api.errors import PublicApiError
from app.core.config import Settings
from app.db.models import Alert, Dlq, Employee, Inquiry, Ticket
from app.db.session import create_db_engine, create_session_factory
from app.main import create_app
from app.schemas.alerts import AlertCreate, DlqCreate
from app.schemas.tickets import TicketCreate, TicketPatch
from app.services.alerts import create_alert, create_dlq
from app.services.tickets import create_ticket, list_admin_tickets, update_admin_ticket

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("OKE_RUN_DB_TESTS") != "1" or not os.environ.get("DATABASE_URL"),
    reason="requires the isolated Compose DB opt-in",
)]


def test_c05_http_routes_persist_and_return_approved_acks():
    settings = Settings(_env_file=None, database_url=os.environ["DATABASE_URL"],
                        internal_api_key=SecretStr("p13-test-internal-key"))
    engine = create_db_engine(settings)
    suffix = uuid4().hex[:12]
    requester = f"p13-http-{suffix}"
    key = f"p13-http-{suffix}"
    workflow = f"p13-http-{suffix}"
    try:
        with create_session_factory(engine).begin() as session:
            session.add(Employee(name=requester, dept="재무팀"))
        app = create_app(settings)
        with TestClient(app) as client:
            request = {"key": key, "title": "합성 HTTP 문의", "requester": requester,
                       "category": "network", "priority": "normal"}
            assert client.post("/tickets", json=request,
                headers={"X-Api-Key": "wrong-test-key"}).status_code == 401
            created = client.post("/tickets", json=request,
                headers={"X-Api-Key": "p13-test-internal-key"})
            replay = client.post("/tickets", json=request,
                headers={"X-Api-Key": "p13-test-internal-key"})
            assert (created.status_code, created.json()["duplicate"]) == (201, False)
            assert (replay.status_code, replay.json()["duplicate"]) == (200, True)
            assert created.json()["ticket_id"] == replay.json()["ticket_id"]

            headers = {"X-Api-Key": "p13-test-internal-key"}
            no_key = {"workflow": workflow, "node": "ticket", "message": "합성 알림",
                      "severity": "high", "ticket_id": created.json()["ticket_id"]}
            first = client.post("/alerts", json=no_key, headers=headers)
            second = client.post("/alerts", json=no_key, headers=headers)
            assert first.status_code == second.status_code == 200
            assert first.json()["duplicate"] is False and first.json()["stored"] == 1
            assert second.json()["duplicate"] is False and second.json()["stored"] == 1
            assert second.json()["count"] == first.json()["count"] + 1

            event = {**no_key, "event_key": f"{workflow}:same"}
            keyed_first = client.post("/alerts", json=event, headers=headers)
            keyed_again = client.post("/alerts", json=event, headers=headers)
            assert keyed_first.json() == {"stored": 1, "count": keyed_first.json()["count"],
                                          "duplicate": False}
            assert keyed_again.json() == {"stored": 0, "count": keyed_first.json()["count"],
                                          "duplicate": True}

            dlq = client.post("/dlq", json={"request_id": None, "workflow": workflow,
                "node": "ticket", "reason": "tickets_down", "safe_payload": {"stage": "ticket"}},
                headers=headers)
            assert dlq.status_code == 200
            assert dlq.json()["stored"] == 1 and dlq.json()["count"] >= 1

        with create_session_factory(engine).begin() as session:
            assert session.scalar(select(Ticket.id).where(Ticket.request_key == key)) is not None
    finally:
        with create_session_factory(engine).begin() as session:
            session.execute(delete(Alert).where(Alert.workflow == workflow))
            session.execute(delete(Dlq).where(Dlq.workflow == workflow))
            session.execute(delete(Ticket).where(Ticket.request_key == key))
            session.execute(delete(Employee).where(Employee.name == requester))
        engine.dispose()


def test_ticket_alert_dlq_transactions_and_ack_boundaries():
    settings = Settings(_env_file=None)
    engine = create_db_engine(settings)
    suffix = uuid4().hex[:12]
    name, other_name, it_name = f"p13-owner-{suffix}", f"p13-other-{suffix}", f"p13-it-{suffix}"
    key = f"p13-{suffix}"
    linked_key = f"p13-web-{suffix}"
    alert_prefix = f"p13-{suffix}"
    ticket_id = None
    try:
        with create_session_factory(engine).begin() as session:
            owner = Employee(name=name, dept="재무팀")
            other = Employee(name=other_name, dept="영업팀")
            it = Employee(name=it_name, dept="IT팀")
            session.add_all([owner, other, it])
            session.flush()
            owner_id = owner.id

        payload = TicketCreate(key=key, title="합성 문의", requester=name,
                               category="network", priority="normal")
        with ThreadPoolExecutor(max_workers=2) as pool:
            ticket_results = list(pool.map(lambda _: create_ticket(settings, payload), range(2)))
        assert sorted(result.duplicate for result in ticket_results) == [False, True]
        assert ticket_results[0].ticket_id == ticket_results[1].ticket_id
        ticket_id = ticket_results[0].ticket_id

        with create_session_factory(engine).begin() as session:
            row = session.scalar(select(Ticket).where(Ticket.request_key == key))
            assert row is not None
            assert session.scalar(select(func.count()).select_from(Ticket)
                                  .where(Ticket.request_key == key)) == 1
            db_ticket_pk = row.id
            it_employee_id = session.scalar(select(Employee.id).where(Employee.name == it_name))
            other_employee_id = session.scalar(select(Employee.id).where(Employee.name == other_name))
        with pytest.raises(PublicApiError) as owner_error:
            create_ticket(settings, TicketCreate(key=key, title="타인 재사용", requester=other_name,
                category="network", priority="normal"))
        assert owner_error.value.status == 403

        with create_session_factory(engine).begin() as session:
            session.add(Inquiry(request_id=linked_key, requester_id=owner_id,
                question="합성 웹 문의", attempt=1, status="completed"))
        linked = create_ticket(settings, TicketCreate(key=linked_key, title="웹 문의 이관",
            requester=name, category="network", priority="normal"))
        with create_session_factory(engine).begin() as session:
            linked_row = session.scalar(select(Ticket).where(Ticket.request_key == linked_key))
            assert linked.duplicate is False and linked_row is not None
            assert linked_row.inquiry_id is not None

        without_key = AlertCreate(workflow=alert_prefix, node="ticket", message="새 알림",
                                  severity="high", ticket_id=ticket_id)
        new_a = create_alert(settings, without_key)
        new_b = create_alert(settings, without_key)
        assert (new_a.stored, new_a.duplicate) == (1, False)
        assert (new_b.stored, new_b.duplicate) == (1, False)
        assert new_b.count == new_a.count + 1

        event_key = f"{alert_prefix}:keyed"
        keyed = AlertCreate(workflow=alert_prefix, node="ticket", message="키 기반 알림",
                            severity="high", ticket_id=ticket_id, event_key=event_key)
        keyed_new = create_alert(settings, keyed)
        keyed_repeat = create_alert(settings, keyed)
        assert (keyed_new.stored, keyed_new.duplicate) == (1, False)
        assert (keyed_repeat.stored, keyed_repeat.duplicate) == (0, True)
        assert keyed_repeat.count == keyed_new.count

        concurrent_key = f"{alert_prefix}:concurrent"
        concurrent_payload = AlertCreate(workflow=alert_prefix, node="ticket", message="동시 알림",
            severity="high", ticket_id=ticket_id, event_key=concurrent_key)
        with ThreadPoolExecutor(max_workers=2) as pool:
            concurrent = list(pool.map(lambda _: create_alert(settings, concurrent_payload), range(2)))
        assert sorted(result.duplicate for result in concurrent) == [False, True]
        assert sum(result.stored for result in concurrent) == 1
        assert concurrent[0].count == concurrent[1].count

        # Alert failure is a separate transaction and cannot undo the committed ticket.
        with pytest.raises(PublicApiError) as alert_error:
            create_alert(settings, AlertCreate(workflow=alert_prefix, node="bad-ticket",
                message="미존재 티켓", severity="high", ticket_id="T-999999999"))
        assert alert_error.value.status == 404
        with create_session_factory(engine).begin() as session:
            assert session.scalar(select(Ticket.id).where(Ticket.id == db_ticket_pk)) == db_ticket_pk

        dlq = create_dlq(settings, DlqCreate(request_id=key, workflow=alert_prefix, node="ticket",
            reason="tickets_down", safe_payload={"stage": "ticket", "api_key": "fake-secret",
                "detail": "user@example.test 010-1234-5678"}))
        assert dlq.stored == 1 and dlq.count >= 1
        with create_session_factory(engine).begin() as session:
            row = session.scalar(select(Dlq).where(Dlq.workflow == alert_prefix))
            assert row is not None
            assert row.safe_payload["api_key"] == "[REDACTED]"
            assert "user@example.test" not in row.safe_payload["detail"]
            assert "010-1234-5678" not in row.safe_payload["detail"]

        updated = update_admin_ticket(settings, ticket_id=db_ticket_pk,
            body=TicketPatch(status="in_progress", assignee=it_employee_id, reply="확인 중"))
        assert updated["status"] == "in_progress" and updated["reply"] == "확인 중"
        assert updated["assignee"] == it_employee_id
        assert updated["ticket_id"] == ticket_id
        assert len(list_admin_tickets(settings)["items"]) >= 1
        with pytest.raises(PublicApiError) as non_it_assignee:
            update_admin_ticket(settings, ticket_id=db_ticket_pk,
                body=TicketPatch(status="open", assignee=other_employee_id))
        assert non_it_assignee.value.status == 400
        cleared = update_admin_ticket(settings, ticket_id=db_ticket_pk,
            body=TicketPatch(status="open", assignee=None))
        assert cleared["assignee"] is None
    finally:
        with create_session_factory(engine).begin() as session:
            session.execute(delete(Alert).where(Alert.workflow == alert_prefix))
            session.execute(delete(Dlq).where(Dlq.workflow == alert_prefix))
            session.execute(delete(Ticket).where(Ticket.request_key.in_([key, linked_key])))
            session.execute(delete(Inquiry).where(Inquiry.request_id == linked_key))
            session.execute(delete(Employee).where(Employee.name.in_([name, other_name, it_name])))
        engine.dispose()
