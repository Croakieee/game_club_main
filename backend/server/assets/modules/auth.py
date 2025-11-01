from fastapi import APIRouter, Header, HTTPException
from .database import *
import bcrypt


def auth_by_uuid(_uuid: str):
    """Авторизация по UUID — теперь сессия закрывается автоматически"""
    with Session() as db:
        exists = db.query(Users).filter(Users.uuid == _uuid).count() == 1
        return True if exists else None


def auth_admin(input_pwd: str) -> bool:
    """Проверка пароля администратора с безопасным закрытием сессии"""
    with Session() as db:
        hashed_password = db.query(Cashout.hashed_password).scalar()
        if not hashed_password:
            return False
        return bcrypt.checkpw(input_pwd.encode("utf-8"), hashed_password.encode("utf-8"))


def auth(authorization: str = Header(description="UUID Пользователя")):
    """Проверка токена авторизации (UUID пользователя)"""
    auth = auth_by_uuid(authorization)
    if not auth:
        raise HTTPException(401, detail="Auth failed")
