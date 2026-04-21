from database import db
from models.category import Category
from models.task import Task
from utils.constants import DEFAULT_CATEGORY_COLOR
from utils.errors import NotFoundError, ValidationError
from utils.helpers import is_valid_color


def list_categories():
    return Category.list_with_task_counts()


def create_category(data):
    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("Nome é obrigatório")

    category = Category()
    category.name = name
    category.description = data.get("description", "")
    category.color = data.get("color", DEFAULT_CATEGORY_COLOR)
    if not is_valid_color(category.color):
        raise ValidationError("Cor inválida")

    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(category_id, data):
    category = Category.get_by_id(category_id)
    if not category:
        raise NotFoundError("Categoria não encontrada")

    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")

    if "name" in data:
        name = data["name"]
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("Nome é obrigatório")
        category.name = name
    if "description" in data:
        description = data["description"]
        category.description = description if isinstance(description, str) else str(description)
    if "color" in data:
        if not is_valid_color(data["color"]):
            raise ValidationError("Cor inválida")
        category.color = data["color"]

    db.session.commit()
    return category.to_dict()


def delete_category(category_id):
    category = Category.get_by_id(category_id)
    if not category:
        raise NotFoundError("Categoria não encontrada")

    for task in Task.list_by_category(category_id):
        task.category_id = None

    db.session.delete(category)
    db.session.commit()
    return {"message": "Categoria deletada"}
