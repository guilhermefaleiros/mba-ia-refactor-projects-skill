import bcrypt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


def hash_password(plain_password, rounds=12):
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_token(user_id, role, secret_key):
    serializer = URLSafeTimedSerializer(secret_key, salt="task-manager-auth")
    return serializer.dumps({"user_id": user_id, "role": role})


def decode_token(token, secret_key, max_age):
    serializer = URLSafeTimedSerializer(secret_key, salt="task-manager-auth")
    try:
        return serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
