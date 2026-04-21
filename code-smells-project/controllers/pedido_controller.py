import logging
import models.pedido as pedido_model
import models.produto as produto_model

logger = logging.getLogger(__name__)

STATUS_VALIDOS = {"pendente", "aprovado", "enviado", "entregue", "cancelado"}

DESCONTO_TIER_ALTO_LIMITE = 10_000
DESCONTO_TIER_MEDIO_LIMITE = 5_000
DESCONTO_TIER_BAIXO_LIMITE = 1_000
TAXA_DESCONTO_ALTO = 0.10
TAXA_DESCONTO_MEDIO = 0.05
TAXA_DESCONTO_BAIXO = 0.02


def listar_por_usuario(usuario_id):
    return pedido_model.get_por_usuario(usuario_id)


def listar_todos():
    return pedido_model.get_todos()


def criar(usuario_id, itens):
    if not usuario_id:
        raise ValueError("Usuario ID é obrigatório")
    if not itens:
        raise ValueError("Pedido deve ter pelo menos 1 item")

    total = 0
    itens_validados = []
    for item in itens:
        produto = produto_model.get_por_id(item["produto_id"])
        if produto is None:
            raise LookupError(f"Produto {item['produto_id']} não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise ValueError(f"Estoque insuficiente para {produto['nome']}")
        total += produto["preco"] * item["quantidade"]
        itens_validados.append({
            "produto_id": item["produto_id"],
            "quantidade": item["quantidade"],
            "preco_unitario": produto["preco"],
        })

    pedido_id = pedido_model.criar_com_itens(usuario_id, total, itens_validados)
    logger.info("Order %d created for user %d, total: %.2f", pedido_id, usuario_id, total)
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(pedido_id, novo_status):
    if novo_status not in STATUS_VALIDOS:
        raise ValueError(f"Status inválido. Válidos: {sorted(STATUS_VALIDOS)}")
    pedido_model.atualizar_status(pedido_id, novo_status)
    logger.info("Order %d status updated to %s", pedido_id, novo_status)


def relatorio_vendas():
    stats = pedido_model.get_stats_vendas()
    faturamento = stats["faturamento"]
    desconto = _calcular_desconto(faturamento)
    return {
        "total_pedidos": stats["total_pedidos"],
        "faturamento_bruto": faturamento,
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": stats["pendentes"],
        "pedidos_aprovados": stats["aprovados"],
        "pedidos_cancelados": stats["cancelados"],
        "ticket_medio": (
            round(faturamento / stats["total_pedidos"], 2)
            if stats["total_pedidos"] > 0
            else 0
        ),
    }


def _calcular_desconto(faturamento):
    if faturamento > DESCONTO_TIER_ALTO_LIMITE:
        return faturamento * TAXA_DESCONTO_ALTO
    if faturamento > DESCONTO_TIER_MEDIO_LIMITE:
        return faturamento * TAXA_DESCONTO_MEDIO
    if faturamento > DESCONTO_TIER_BAIXO_LIMITE:
        return faturamento * TAXA_DESCONTO_BAIXO
    return 0
