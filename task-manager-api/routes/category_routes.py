from flask import Blueprint, jsonify, request

from controllers.category_controller import (
    create_category,
    delete_category,
    list_categories,
    update_category,
)
from middleware.auth import require_admin
from utils.errors import ValidationError


category_bp = Blueprint("categories", __name__)


@category_bp.route("/categories", methods=["GET"])
@require_admin
def get_categories():
    return jsonify(list_categories()), 200


@category_bp.route("/categories", methods=["POST"])
@require_admin
def create_category_route():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Dados inválidos")
    return jsonify(create_category(data)), 201


@category_bp.route("/categories/<int:cat_id>", methods=["PUT"])
@require_admin
def update_category_route(cat_id):
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Dados inválidos")
    return jsonify(update_category(cat_id, data)), 200


@category_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
@require_admin
def delete_category_route(cat_id):
    return jsonify(delete_category(cat_id)), 200
