from flask import Blueprint, current_app, jsonify, request

from controllers.user_controller import (
    create_user,
    delete_user,
    get_user,
    get_user_tasks,
    list_users,
    login,
    update_user,
)
from middleware.auth import require_admin, require_auth, require_self_or_admin
from utils.errors import ValidationError


user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
@require_admin
def get_users():
    return jsonify(list_users()), 200


@user_bp.route("/users/<int:user_id>", methods=["GET"])
@require_auth
def get_user_route(user_id):
    require_self_or_admin(user_id)
    return jsonify(get_user(user_id)), 200


@user_bp.route("/users", methods=["POST"])
def create_user_route():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Dados inválidos")
    return jsonify(create_user(data, current_app.config["BCRYPT_ROUNDS"])), 201


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
@require_auth
def update_user_route(user_id):
    require_self_or_admin(user_id)
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Dados inválidos")
    return jsonify(update_user(user_id, data, current_app.config["BCRYPT_ROUNDS"])), 200


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@require_auth
def delete_user_route(user_id):
    require_self_or_admin(user_id)
    return jsonify(delete_user(user_id)), 200


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
@require_auth
def get_user_tasks_route(user_id):
    require_self_or_admin(user_id)
    return jsonify(get_user_tasks(user_id)), 200


@user_bp.route("/login", methods=["POST"])
def login_route():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Dados inválidos")
    return jsonify(login(data, current_app.config["SECRET_KEY"])), 200
