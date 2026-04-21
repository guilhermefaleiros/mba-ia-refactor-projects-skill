import logging
from models.database import get_db

logger = logging.getLogger(__name__)

_PUBLIC_FIELDS = {"id", "nome", "email", "tipo", "criado_em"}


def _serialize_public(row):
    return {k: row[k] for k in _PUBLIC_FIELDS if k in row.keys()}


def get_todos(db=None):
    db = db or get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios")
    return [_serialize_public(row) for row in cursor.fetchall()]


def get_por_id(id, db=None):
    db = db or get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
    row = cursor.fetchone()
    return _serialize_public(row) if row else None


def get_por_email(email, db=None):
    """Return full row including hashed senha — for internal auth use only. Never send to client."""
    db = db or get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    return dict(row) if row else None


def criar(nome, email, senha_hash, tipo="cliente", db=None):
    db = db or get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid
