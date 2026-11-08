"""Seed/verify/clean P1-4 persistence fixtures across a Compose DB restart."""

import hashlib
import os

import pytest
from sqlalchemy import delete, func, select

from app.db.models import Alert, Chunk, Document, Dlq, Employee, Inquiry, Ticket
from app.db.session import create_db_engine, create_session_factory

pytestmark = [pytest.mark.integration, pytest.mark.skipif(
    os.environ.get("OKE_RUN_DB_TESTS") != "1" or not os.environ.get("DATABASE_URL"),
    reason="requires the isolated Compose DB opt-in",
)]


def _identifiers() -> tuple[str, str]:
    run_id = os.environ.get("P1_4_RUN_ID", "")
    assert run_id and run_id.isalnum() and len(run_id) <= 32
    return f"p14-{run_id}", f"p14-doc-{run_id}"


def test_persistence_phase():
    phase = os.environ.get("P1_4_PHASE")
    if phase not in {"seed", "verify", "cleanup"}:
        pytest.skip("run through deploy/check_persistence.py to preserve the restart boundary")
    request_key, doc_key = _identifiers()
    content = f"Synthetic persistence fixture {doc_key}"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    engine = create_db_engine()
    sessions = create_session_factory(engine)
    try:
        if phase == "seed":
            with sessions.begin() as session:
                # A retry can clean only the uniquely named fixture from this run.
                doc = session.scalar(select(Document).where(Document.doc_key == doc_key))
                if doc:
                    session.execute(delete(Chunk).where(Chunk.document_id == doc.id))
                    session.delete(doc)
                employee = session.scalar(select(Employee).where(Employee.name == request_key))
                if employee:
                    session.execute(delete(Alert).where(Alert.workflow == request_key))
                    session.execute(delete(Dlq).where(Dlq.workflow == request_key))
                    session.execute(delete(Ticket).where(Ticket.request_key == request_key))
                    session.execute(delete(Inquiry).where(Inquiry.request_id == request_key))
                    session.delete(employee)
                employee = Employee(name=request_key, dept="재무팀")
                session.add(employee)
                session.flush()
                inquiry = Inquiry(request_id=request_key, requester_id=employee.id,
                    question="Synthetic persistence inquiry", attempt=1,
                    result={"marker": request_key}, status="completed")
                session.add(inquiry)
                session.flush()
                ticket = Ticket(request_key=request_key, inquiry_id=inquiry.id,
                    requester_id=employee.id, title="Synthetic persistence ticket",
                    category="network", priority="normal")
                session.add(ticket)
                session.flush()
                session.add_all([
                    Alert(ticket_id=ticket.id, event_key=request_key,
                        workflow=request_key, node="p1-4", message="Synthetic alert",
                        severity="low"),
                    Dlq(request_id=request_key, workflow=request_key, node="p1-4",
                        reason="synthetic", safe_payload={"marker": request_key},
                        status="pending"),
                ])
                document = Document(doc_key=doc_key, title="Synthetic persistence document",
                    access_level="all", source_url=None, source_hash=digest)
                session.add(document)
                session.flush()
                session.add(Chunk(document_id=document.id, chunk_no=0,
                    section="Synthetic section", content=content, content_hash=digest,
                    embedding=[0.0] * 3072, embedding_model="fixture-only",
                    metadata_={"run_id": request_key, "fixture": True}))
            return

        if phase == "verify":
            with sessions.begin() as session:
                employee = session.scalar(select(Employee).where(Employee.name == request_key))
                inquiry = session.scalar(select(Inquiry).where(Inquiry.request_id == request_key))
                ticket = session.scalar(select(Ticket).where(Ticket.request_key == request_key))
                alert = session.scalar(select(Alert).where(Alert.event_key == request_key))
                dlq = session.scalar(select(Dlq).where(Dlq.workflow == request_key))
                document = session.scalar(select(Document).where(Document.doc_key == doc_key))
                assert all((employee, inquiry, ticket, alert, dlq, document))
                assert inquiry.result == {"marker": request_key}
                assert ticket.inquiry_id == inquiry.id and ticket.requester_id == employee.id
                assert alert.ticket_id == ticket.id and alert.event_key == request_key
                assert dlq.safe_payload == {"marker": request_key}
                chunk = session.scalar(select(Chunk).where(Chunk.document_id == document.id))
                assert chunk is not None and len(chunk.embedding) == 3072
                assert chunk.metadata_ == {"run_id": request_key, "fixture": True}
                assert chunk.content_hash == hashlib.sha256(
                    chunk.content.encode("utf-8")).hexdigest()
                assert session.scalar(select(func.count()).select_from(Chunk).where(
                    Chunk.document_id == document.id)) == 1
            return

        with sessions.begin() as session:
            document = session.scalar(select(Document).where(Document.doc_key == doc_key))
            if document:
                session.execute(delete(Chunk).where(Chunk.document_id == document.id))
                session.delete(document)
            session.execute(delete(Alert).where(Alert.event_key == request_key))
            session.execute(delete(Dlq).where(Dlq.workflow == request_key))
            session.execute(delete(Ticket).where(Ticket.request_key == request_key))
            session.execute(delete(Inquiry).where(Inquiry.request_id == request_key))
            session.execute(delete(Employee).where(Employee.name == request_key))
    finally:
        engine.dispose()
