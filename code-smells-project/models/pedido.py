import logging
from models.database import get_db

logger = logging.getLogger(__name__)


def criar_com_itens(usuario_id, total, itens_validados, db=None):
    """Create order and all items in a single transaction.

    itens_validados: list of {produto_id, quantidade, preco_unitario}
    Also decrements stock for each product.
    Returns the new pedido_id.
    """
    db = db or get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid

    for item in itens_validados:
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)"
            " VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
        )
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )

    db.commit()
    return pedido_id


def get_por_usuario(usuario_id, db=None):
    db = db or get_db()
    return _get_pedidos_com_itens(db, "WHERE p.usuario_id = ?", (usuario_id,))


def get_todos(db=None):
    db = db or get_db()
    return _get_pedidos_com_itens(db)


def atualizar_status(pedido_id, novo_status, db=None):
    db = db or get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id),
    )
    db.commit()


def get_stats_vendas(db=None):
    db = db or get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM pedidos")
    faturamento = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
    cancelados = cursor.fetchone()[0]

    return {
        "total_pedidos": total_pedidos,
        "faturamento": round(faturamento, 2),
        "pendentes": pendentes,
        "aprovados": aprovados,
        "cancelados": cancelados,
    }


def _get_pedidos_com_itens(db, where_clause="", params=()):
    cursor = db.cursor()
    query = """
        SELECT
            p.id          AS pedido_id,
            p.usuario_id,
            p.status,
            p.total,
            p.criado_em,
            ip.produto_id,
            ip.quantidade,
            ip.preco_unitario,
            pr.nome       AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        {where}
        ORDER BY p.id
    """.format(where=where_clause)
    cursor.execute(query, params)

    pedidos = {}
    for row in cursor.fetchall():
        pid = row["pedido_id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
        if row["produto_id"]:
            pedidos[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())
