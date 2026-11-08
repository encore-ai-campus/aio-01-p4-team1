"""Explicit model registration for Alembic; never calls create_all or seeds data."""

from app.db.models.employees import Employee
from app.db.models.users import User
from app.db.models.sessions import Session
from app.db.models.inquiries import Inquiry
from app.db.models.tickets import Ticket
from app.db.models.alerts import Alert
from app.db.models.dlq import Dlq
from app.db.models.rag import Document, Chunk

__all__ = ["Employee", "User", "Session", "Inquiry", "Ticket", "Alert", "Dlq", "Document", "Chunk"]
