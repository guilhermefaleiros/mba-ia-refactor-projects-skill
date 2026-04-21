from flask import Blueprint, jsonify, request

from controllers.task_controller import (
    create_task,
    delete_task,
    get_task,
    list_tasks,
    search_tasks,
    task_stats,
    update_task,
)
from middleware.auth import require_auth
from utils.errors import ValidationError


task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
@require_auth
def get_tasks():
    return jsonify(list_tasks()), 200


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
@require_auth
def get_task_route(task_id):
    return jsonify(get_task(task_id)), 200


@task_bp.route("/tasks", methods=["POST"])
@require_auth
def create_task_route():
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Dados inválidos")
    return jsonify(create_task(data)), 201


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@require_auth
def update_task_route(task_id):
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Dados inválidos")
    return jsonify(update_task(task_id, data)), 200


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@require_auth
def delete_task_route(task_id):
    return jsonify(delete_task(task_id)), 200


@task_bp.route("/tasks/search", methods=["GET"])
@require_auth
def search_tasks_route():
    return jsonify(
        search_tasks(
            query=request.args.get("q", ""),
            status=request.args.get("status", ""),
            priority=request.args.get("priority"),
            user_id=request.args.get("user_id"),
        )
    ), 200


@task_bp.route("/tasks/stats", methods=["GET"])
@require_auth
def task_stats_route():
    return jsonify(task_stats()), 200
