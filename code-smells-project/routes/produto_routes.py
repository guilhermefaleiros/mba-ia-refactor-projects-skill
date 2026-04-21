from flask import Blueprint, request, jsonify
import controllers.produto_controller as produto_controller

produto_bp = Blueprint("produto", __name__)


@produto_bp.route("/produtos", methods=["GET"])
def listar_produtos():
    return jsonify({"dados": produto_controller.listar(), "sucesso": True}), 200


@produto_bp.route("/produtos/busca", methods=["GET"])
def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria")
    preco_min = request.args.get("preco_min")
    preco_max = request.args.get("preco_max")
    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)
    resultados = produto_controller.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


@produto_bp.route("/produtos/<int:id>", methods=["GET"])
def buscar_produto(id):
    produto = produto_controller.buscar_por_id(id)
    return jsonify({"dados": produto, "sucesso": True}), 200


@produto_bp.route("/produtos", methods=["POST"])
def criar_produto():
    dados = request.get_json()
    resultado = produto_controller.criar(dados)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Produto criado"}), 201


@produto_bp.route("/produtos/<int:id>", methods=["PUT"])
def atualizar_produto(id):
    dados = request.get_json()
    produto_controller.atualizar(id, dados)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@produto_bp.route("/produtos/<int:id>", methods=["DELETE"])
def deletar_produto(id):
    produto_controller.deletar(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
