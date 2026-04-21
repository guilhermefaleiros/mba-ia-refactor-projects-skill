import logging
from models.database import get_db

logger = logging.getLogger(__name__)

_PUBLIC_FIELDS = {"id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em"}


def _serialize(row):
    return {k: row[k] for k in _PUBLIC_FIELDS if k in row.keys()}


def get_todos(db=None):
    db = db or get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos")
    return [_serialize(row) for row in cursor.fetchall()]


def get_por_id(id, db=None):
    db = db or get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
    row = cursor.fetchone()
    return _serialize(row) if row else None


def criar(nome, descricao, preco, estoque, categoria, db=None):
    db = db or get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar(id, nome, descricao, preco, estoque, categoria, db=None):
    db = db or get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, id),
    )
    db.commit()


def deletar(id, db=None):
    db = db or get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
    db.commit()


def buscar(termo=None, categoria=None, preco_min=None, preco_max=None, db=None):
    db = db or get_db()
    cursor = db.cursor()
    conditions = []
    params = []

    if termo:
        conditions.append("(nome LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        conditions.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        conditions.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        conditions.append("preco <= ?")
        params.append(preco_max)

    query = "SELECT * FROM produtos"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, params)
    return [_serialize(row) for row in cursor.fetchall()]
