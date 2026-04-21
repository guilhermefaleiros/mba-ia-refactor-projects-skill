from functools import wraps

from flask import current_app, g, request

from models.user import User
from utils.errors import ForbiddenError, UnauthorizedError
from utils.security import decode_token


def _get_current_user():
    user = getattr(g, "current_user", None)
    if user is None:
        raise UnauthorizedError("Não autorizado")
    return user


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise UnauthorizedError("Não autorizado")

        token = auth_header.removeprefix("Bearer ").strip()
        payload = decode_token(
            token,
            current_app.config["SECRET_KEY"],
            current_app.config["TOKEN_MAX_AGE"],
        )
        if not payload:
            raise UnauthorizedError("Token inválido")

        user = User.get_by_id(payload.get("user_id"))
        if not user or not user.active:
            raise UnauthorizedError("Não autorizado")

        g.current_user = user
        g.current_user_payload = payload
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise UnauthorizedError("Não autorizado")

        token = auth_header.removeprefix("Bearer ").strip()
        payload = decode_token(
            token,
            current_app.config["SECRET_KEY"],
            current_app.config["TOKEN_MAX_AGE"],
        )
        if not payload:
            raise UnauthorizedError("Token inválido")

        user = User.get_by_id(payload.get("user_id"))
        if not user or not user.active:
            raise UnauthorizedError("Não autorizado")
        if not user.is_admin():
            raise ForbiddenError("Acesso negado")

        g.current_user = user
        g.current_user_payload = payload
        return fn(*args, **kwargs)

    return wrapper


def require_self_or_admin(user_id):
    user = _get_current_user()
    if not user.is_admin() and user.id != int(user_id):
        raise ForbiddenError("Acesso negado")
