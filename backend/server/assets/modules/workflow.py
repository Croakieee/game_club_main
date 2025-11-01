from .database import *
from datetime import datetime
from uuid import uuid4
from sqlalchemy import and_, select

# Предполагается =), что DATE_FORMAT_DEFAULT определён в этом модуле или импортируется выше по проекту.
# Если он в другом месте ну пиздец =(.


def create_user(data) -> str:
    """Создание пользователя. Бросает исключение, если логин уже существует."""
    if login_user(data):
        raise Exception("User already registred")

    with Session() as db:
        new_uuid = str(uuid4())
        new_user = Users(uuid=new_uuid, name=data.name, login=data.login, password=data.password)
        db.add(new_user)
        db.commit()
        return new_uuid


def login_user(data) -> dict | None:
    """Логин: возвращает словарь с uuid/name или None."""
    with Session() as db:
        user = (
            db.query(Users.uuid, Users.name)
            .filter(and_(Users.login == data.login, Users.password == data.password))
            .first()
        )
        if user:
            return {"uuid": user.uuid, "name": user.name}
        return None


def get_name_by_uuid(_uuid: str) -> str:
    with Session() as db:
        name = db.scalars(select(Users.name).where(Users.uuid == _uuid)).one()
        return name


def get_session_start_time(sessionId: str) -> str:
    with Session() as db:
        start_time = db.scalars(select(Sessions.start).where(Sessions.uuid == sessionId)).one()
        return start_time


def start_session(user_uuid: str) -> str:
    session_id = str(uuid4())
    dt_start = datetime.now().strftime(DATE_FORMAT_DEFAULT)
    with Session() as db:
        new_session = Sessions(uuid=session_id, user_uuid=user_uuid, start=dt_start, status="work")
        db.add(new_session)
        db.commit()
    return session_id


def finish_session(session_id: str) -> None:
    dt_finish = datetime.now().strftime(DATE_FORMAT_DEFAULT)
    with Session() as db:
        user_session = db.scalars(select(Sessions).where(Sessions.uuid == session_id)).one()
        user_session.finish = dt_finish
        user_session.status = "closed"
        db.commit()


def get_all_users() -> list[dict]:
    with Session() as db:
        users = db.query(Users.name, Users.uuid).all()
        return [{"name": u.name, "uuid": u.uuid} for u in users]


def get_cashout() -> float:
    with Session() as db:
        balance = db.query(Cashout).first().balance
        return float(balance)


def edit_cashout(amount: float, reason: str) -> None:
    """
    Изменяет баланс кассы и пишет запись в историю в одной транзакции.
    """
    with Session() as db:
        row = db.query(Cashout).first()
        new_value = float(row.balance) + amount

        now = datetime.now().strftime(DATE_FORMAT_DEFAULT)
        db.add(
            CashoutHistory(
                old_value=row.balance,
                new_value=new_value,
                reason=reason,
                edit_date=now,
            )
        )

        row.balance = new_value
        db.commit()


def set_cashout(amount: float) -> None:
    """
    Админская установка баланса кассы с записью в историю.
    """
    with Session() as db:
        row = db.query(Cashout).first()
        old_value = float(row.balance)
        row.balance = amount

        now = datetime.now().strftime(DATE_FORMAT_DEFAULT)
        db.add(
            CashoutHistory(
                old_value=old_value,
                new_value=amount,
                reason="Admin",
                edit_date=now,
            )
        )
        db.commit()
