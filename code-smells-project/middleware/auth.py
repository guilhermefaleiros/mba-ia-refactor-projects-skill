import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


def require_auth(f):
    """Authentication decorator. Apply to routes that require a logged-in user.

    Currently a stub — implement JWT verification here.
    Expected header: Authorization: Bearer <token>

    To implement:
      1. pip install PyJWT
      2. Decode the token with jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
      3. Store the payload on flask.g or request context for downstream use
      4. Return 401 if the token is missing or invalid
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # TODO: Replace this stub with real JWT verification before going to production.
        # token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        # if not token:
        #     return jsonify({"erro": "Não autorizado", "sucesso": False}), 401
        # try:
        #     payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        #     request.current_user_id = payload["sub"]
        # except jwt.InvalidTokenError:
        #     return jsonify({"erro": "Token inválido", "sucesso": False}), 401
        return f(*args, **kwargs)
    return decorated
