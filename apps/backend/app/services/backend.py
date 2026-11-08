"""Database-backed services for authentication, inquiry and P1-3 operations."""

import anyio
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.session import DatabaseConfigurationError, create_db_engine, create_session_factory
from app.services.accounts import (AccountError, account_items, create_account,
                                   create_employee, delete_account, employee_items,
                                   reset_password, update_active)
from app.services.auth import LoginError, authenticate, change_password, logout
from app.services.inquiries import ask_support, my_requests
from app.services.alerts import create_alert, create_dlq, list_admin_alerts
from app.services.tickets import create_ticket, list_admin_tickets, update_admin_ticket


class DatabaseBackend:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def execute(self, operation: str, *, body=None, principal=None, entity_id=None,
                      session_id=None):
        try:
            if operation == "ask":
                return await ask_support(self.settings, body=body, principal=principal)
            return await anyio.to_thread.run_sync(
                lambda: self._execute_sync(operation, body, principal, entity_id, session_id))
        except LoginError:
            raise HTTPException(401) from None
        except AccountError as error:
            raise HTTPException(error.status, detail={"code": error.code, "message": error.message}) from None
        except SQLAlchemyError:
            raise HTTPException(503) from None
        except DatabaseConfigurationError:
            raise HTTPException(503) from None

    def _execute_sync(self, operation, body, principal, entity_id, session_id):
        if operation == "create_ticket":
            return create_ticket(self.settings, body)
        if operation == "create_alert":
            return create_alert(self.settings, body)
        if operation == "create_dlq":
            return create_dlq(self.settings, body)
        if operation == "tickets":
            return list_admin_tickets(self.settings)
        if operation == "update_ticket":
            return update_admin_ticket(self.settings, ticket_id=entity_id, body=body)
        if operation == "alerts":
            return list_admin_alerts(self.settings)
        if not self.settings.database_url:
            raise HTTPException(503)
        if operation == "my_requests":
            return my_requests(self.settings, user_id=principal.id)
        engine = create_db_engine(self.settings)
        try:
            with create_session_factory(engine).begin() as session:
                if operation == "login":
                    secret = self.settings.session_secret
                    if not secret or not secret.get_secret_value():
                        raise HTTPException(503)
                    summary, token = authenticate(session, login_id=body.login_id,
                        password=body.password.get_secret_value(), session_secret=secret.get_secret_value())
                    return {"user": summary, "_token": token}
                if operation == "logout":
                    logout(session, session_id)
                    return {"ok": True}
                if operation == "change_password":
                    return change_password(session, principal_id=principal.id, session_id=session_id,
                        current_password=body.current_password.get_secret_value(),
                        new_password=body.new_password.get_secret_value())
                if operation == "employees":
                    return {"items": employee_items(session)}
                if operation == "create_employee":
                    return create_employee(session, name=body.name, dept=body.dept)
                if operation == "users":
                    return {"items": account_items(session)}
                if operation == "create_user":
                    return create_account(session, employee_id=body.employee_id, login_id=body.login_id,
                                          password=body.temporary_password.get_secret_value())
                if operation == "update_user":
                    return update_active(session, user_id=entity_id, actor_id=principal.id,
                                         is_active=body.is_active)
                if operation == "delete_user":
                    return delete_account(session, user_id=entity_id, actor_id=principal.id)
                if operation == "reset_password":
                    return reset_password(session, user_id=entity_id,
                                          password=body.temporary_password.get_secret_value())
                raise HTTPException(501)
        finally:
            engine.dispose()
