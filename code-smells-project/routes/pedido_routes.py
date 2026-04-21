from flask import Blueprint, request, jsonify
import controllers.pedido_controller as pedido_controller
from models.database import get_db

pedido_bp = Blueprint("pedido", __name__)


@pedido_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos", "sucesso": False}), 400
    resultado = pedido_controller.criar(
        dados.get("usuario_id"),
        dados.get("itens", []),
    )
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@pedido_bp.route("/pedidos", methods=["GET"])
def listar_todos_pedidos():
    return jsonify({"dados": pedido_controller.listar_todos(), "sucesso": True}), 200


@pedido_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_controller.listar_por_usuario(usuario_id), "sucesso": True}), 200


@pedido_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    pedido_controller.atualizar_status(pedido_id, dados.get("status", "") if dados else "")
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


@pedido_bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    return jsonify({"dados": pedido_controller.relatorio_vendas(), "sucesso": True}), 200


@pedido_bp.route("/health", methods=["GET"])
def health_check():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT 1")
    cursor.execute("SELECT COUNT(*) FROM produtos")
    produtos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    usuarios = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    pedidos = cursor.fetchone()[0]
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
    }), 200
