from database import db
from models.task import Task
from models.user import User
from utils.constants import MIN_PASSWORD_LENGTH, VALID_USER_ROLES
from utils.errors import ForbiddenError, NotFoundError, ValidationError
from utils.helpers import validate_email
from utils.security import create_token


def _serialize_task(task):
    data = task.to_dict()
    data["overdue"] = task.is_overdue()
    return data


def list_users():
    return User.list_with_task_counts()


def get_user(user_id):
    user = User.get_by_id(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    data = user.to_dict()
    data["tasks"] = [_serialize_task(task) for task in Task.list_by_user(user_id)]
    return data


def create_user(data, bcrypt_rounds):
    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    if not isinstance(name, str) or not name.strip():
        raise ValidationError("Nome é obrigatório")
    if not isinstance(email, str) or not email.strip():
        raise ValidationError("Email é obrigatório")
    if not validate_email(email):
        raise ValidationError("Email inválido")
    if not isinstance(password, str) or not password:
        raise ValidationError("Senha é obrigatória")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError("Senha deve ter no mínimo 4 caracteres")
    if role not in VALID_USER_ROLES:
        raise ValidationError("Role inválido")
    if User.find_by_email(email):
        raise ValidationError("Email já cadastrado")

    user = User()
    user.name = name
    user.email = email
    user.set_password(password, bcrypt_rounds)
    user.role = role

    db.session.add(user)
    db.session.commit()
    return user.to_dict()


def update_user(user_id, data, bcrypt_rounds):
    user = User.get_by_id(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")

    if "name" in data:
        name = data["name"]
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("Nome é obrigatório")
        user.name = name

    if "email" in data:
        email = data["email"]
        if not validate_email(email):
            raise ValidationError("Email inválido")
        existing = User.find_by_email(email)
        if existing and existing.id != user_id:
            raise ValidationError("Email já cadastrado")
        user.email = email

    if "password" in data:
        password = data["password"]
        if not isinstance(password, str) or not password:
            raise ValidationError("Senha é obrigatória")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError("Senha muito curta")
        user.set_password(password, bcrypt_rounds)

    if "role" in data:
        role = data["role"]
        if role not in VALID_USER_ROLES:
            raise ValidationError("Role inválido")
        user.role = role

    if "active" in data:
        user.active = bool(data["active"])

    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = User.get_by_id(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    for task in Task.list_by_user(user_id):
        db.session.delete(task)

    db.session.delete(user)
    db.session.commit()
    return {"message": "Usuário deletado com sucesso"}


def get_user_tasks(user_id):
    user = User.get_by_id(user_id)
    if not user:
        raise NotFoundError("Usuário não encontrado")

    result = []
    for task in Task.list_by_user(user_id):
        data = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "created_at": str(task.created_at),
            "due_date": str(task.due_date) if task.due_date else None,
            "overdue": task.is_overdue(),
        }
        result.append(data)
    return result


def login(data, secret_key):
    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not email.strip() or not isinstance(password, str) or not password:
        raise ValidationError("Email e senha são obrigatórios")

    user = User.find_by_email(email)
    if not user or not user.check_password(password):
        raise ValidationError("Credenciais inválidas")
    if not user.active:
        raise ForbiddenError("Usuário inativo")

    token = create_token(user.id, user.role, secret_key)
    return {
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
        "token": token,
    }
