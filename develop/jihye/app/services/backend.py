"""P1-1 database operations. Unimplemented business routes remain fail-closed."""

import anyio
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.session import DatabaseConfigurationError, create_db_engine, create_session_factory
from app.services.accounts import (AccountError, account_items, create_account,
                                   employee_items, reset_password, update_active)
from app.services.auth import LoginError, authenticate, change_password, logout


class DatabaseBackend:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def execute(self, operation: str, *, body=None, principal=None, entity_id=None,
                      session_id=None):
        try:
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
        if not self.settings.database_url:
            raise HTTPException(503)
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
                if operation == "users":
                    return {"items": account_items(session)}
                if operation == "create_user":
                    return create_account(session, employee_id=body.employee_id, login_id=body.login_id,
                                          password=body.temporary_password.get_secret_value())
                if operation == "update_user":
                    return update_active(session, user_id=entity_id, actor_id=principal.id,
                                         is_active=body.is_active)
                if operation == "reset_password":
                    return reset_password(session, user_id=entity_id,
                                          password=body.temporary_password.get_secret_value())
                raise HTTPException(501)
        finally:
            engine.dispose()
