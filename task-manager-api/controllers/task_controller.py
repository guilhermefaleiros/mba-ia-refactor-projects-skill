from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.constants import (
    DEFAULT_PRIORITY,
    TASK_PRIORITY_MAX,
    TASK_PRIORITY_MIN,
    TASK_TITLE_MAX_LENGTH,
    TASK_TITLE_MIN_LENGTH,
    VALID_TASK_STATUSES,
)
from utils.errors import NotFoundError, ValidationError
from utils.helpers import calculate_percentage, normalize_tags, parse_date
from utils.time import utcnow


def _serialize_task(task, include_related=True):
    data = task.to_dict()
    if include_related:
        data["user_name"] = task.user.name if task.user else None
        data["category_name"] = task.category.name if task.category else None
        data["overdue"] = task.is_overdue()
    return data


def _validate_task_payload(data, partial=False):
    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")

    payload = {}

    if "title" in data:
        title = data.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValidationError("Título é obrigatório")
        if len(title) < TASK_TITLE_MIN_LENGTH:
            raise ValidationError("Título muito curto")
        if len(title) > TASK_TITLE_MAX_LENGTH:
            raise ValidationError("Título muito longo")
        payload["title"] = title
    elif not partial:
        raise ValidationError("Título é obrigatório")

    if "description" in data:
        description = data.get("description", "")
        payload["description"] = description if isinstance(description, str) else str(description)

    if "status" in data:
        status = data.get("status", "pending")
        if status not in VALID_TASK_STATUSES:
            raise ValidationError("Status inválido")
        payload["status"] = status
    elif not partial:
        payload["status"] = "pending"

    if "priority" in data:
        try:
            priority = int(data.get("priority", DEFAULT_PRIORITY))
        except (TypeError, ValueError):
            raise ValidationError("Prioridade inválida")
        if priority < TASK_PRIORITY_MIN or priority > TASK_PRIORITY_MAX:
            raise ValidationError("Prioridade deve ser entre 1 e 5")
        payload["priority"] = priority
    elif not partial:
        payload["priority"] = DEFAULT_PRIORITY

    if "user_id" in data:
        user_id = data.get("user_id")
        if user_id is not None:
            user = User.get_by_id(int(user_id))
            if not user:
                raise NotFoundError("Usuário não encontrado")
        payload["user_id"] = int(user_id) if user_id is not None else None

    if "category_id" in data:
        category_id = data.get("category_id")
        if category_id is not None:
            category = Category.get_by_id(int(category_id))
            if not category:
                raise NotFoundError("Categoria não encontrada")
        payload["category_id"] = int(category_id) if category_id is not None else None

    if "due_date" in data:
        due_date = data.get("due_date")
        payload["due_date"] = parse_date(due_date) if due_date else None

    if "tags" in data:
        payload["tags"] = normalize_tags(data.get("tags"))

    return payload


def list_tasks():
    return [_serialize_task(task) for task in Task.list_all_with_relations()]


def get_task(task_id):
    task = Task.get_by_id_with_relations(task_id)
    if not task:
        raise NotFoundError("Task não encontrada")
    return _serialize_task(task)


def create_task(data):
    payload = _validate_task_payload(data)
    task = Task()
    task.title = payload["title"]
    task.description = payload.get("description", "")
    task.status = payload.get("status", "pending")
    task.priority = payload.get("priority", DEFAULT_PRIORITY)
    task.user_id = payload.get("user_id")
    task.category_id = payload.get("category_id")
    task.due_date = payload.get("due_date")
    task.tags = payload.get("tags")

    db.session.add(task)
    db.session.commit()
    return _serialize_task(Task.get_by_id_with_relations(task.id))


def update_task(task_id, data):
    task = Task.get_by_id(task_id)
    if not task:
        raise NotFoundError("Task não encontrada")

    payload = _validate_task_payload(data, partial=True)
    for key, value in payload.items():
        setattr(task, key, value)

    task.updated_at = utcnow()
    db.session.commit()
    return _serialize_task(Task.get_by_id_with_relations(task.id))


def delete_task(task_id):
    task = Task.get_by_id(task_id)
    if not task:
        raise NotFoundError("Task não encontrada")

    db.session.delete(task)
    db.session.commit()
    return {"message": "Task deletada com sucesso"}


def search_tasks(query="", status="", priority=None, user_id=None):
    tasks = Task.search(query=query, status=status, priority=priority, user_id=user_id)
    return [_serialize_task(task) for task in tasks]


def task_stats():
    total = Task.count_all()
    done = Task.count_by_status("done")
    pending = Task.count_by_status("pending")
    in_progress = Task.count_by_status("in_progress")
    cancelled = Task.count_by_status("cancelled")
    overdue = Task.count_overdue()

    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "done": done,
        "cancelled": cancelled,
        "overdue": overdue,
        "completion_rate": calculate_percentage(done, total),
    }


def user_tasks(user_id):
    user = User.get_by_id(int(user_id))
    if not user:
        raise NotFoundError("Usuário não encontrado")

    return [_serialize_task(task, include_related=False) for task in Task.list_by_user(int(user_id))]
