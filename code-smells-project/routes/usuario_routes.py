from flask import Blueprint, request, jsonify
import controllers.usuario_controller as usuario_controller

usuario_bp = Blueprint("usuario", __name__)


@usuario_bp.route("/usuarios", methods=["GET"])
def listar_usuarios():
    return jsonify({"dados": usuario_controller.listar(), "sucesso": True}), 200


@usuario_bp.route("/usuarios/<int:id>", methods=["GET"])
def buscar_usuario(id):
    usuario = usuario_controller.buscar_por_id(id)
    return jsonify({"dados": usuario, "sucesso": True}), 200


@usuario_bp.route("/usuarios", methods=["POST"])
def criar_usuario():
    dados = request.get_json()
    resultado = usuario_controller.criar(dados)
    return jsonify({"dados": resultado, "sucesso": True}), 201


@usuario_bp.route("/login", methods=["POST"])
def login():
    dados = request.get_json()
    usuario = usuario_controller.login(dados)
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
