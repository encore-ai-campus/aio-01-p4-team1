from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Employee, User


def get_user_by_login(session: Session, login_id: str):
    return session.scalar(select(User).where(User.login_id == login_id))


def get_user_identity(session: Session, user_id: int):
    return session.execute(select(User, Employee).join(Employee, Employee.id == User.employee_id)
                           .where(User.id == user_id)).one_or_none()


def list_users(session: Session):
    return session.execute(select(User, Employee).join(Employee, Employee.id == User.employee_id)
                           .order_by(User.id)).all()


def list_employees(session: Session):
    return session.execute(select(Employee, User.id).outerjoin(User, User.employee_id == Employee.id)
                           .order_by(Employee.id)).all()
