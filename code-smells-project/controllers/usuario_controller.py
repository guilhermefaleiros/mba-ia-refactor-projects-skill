import logging
import models.usuario as usuario_model
from utils.security import hash_password, verify_password

logger = logging.getLogger(__name__)


def listar():
    return usuario_model.get_todos()


def buscar_por_id(id):
    usuario = usuario_model.get_por_id(id)
    if usuario is None:
        raise LookupError("Usuário não encontrado")
    return usuario


def criar(dados):
    if not dados:
        raise ValueError("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValueError("Nome, email e senha são obrigatórios")
    senha_hash = hash_password(senha)
    id = usuario_model.criar(nome, email, senha_hash)
    logger.info("User created: %s", email)
    return {"id": id}


def login(dados):
    if not dados:
        raise ValueError("Dados inválidos")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ValueError("Email e senha são obrigatórios")
    usuario_row = usuario_model.get_por_email(email)
    if usuario_row is None or not verify_password(senha, usuario_row["senha"]):
        logger.info("Login failed: %s", email)
        raise PermissionError("Email ou senha inválidos")
    logger.info("Login successful: %s", email)
    return {
        "id": usuario_row["id"],
        "nome": usuario_row["nome"],
        "email": usuario_row["email"],
        "tipo": usuario_row["tipo"],
    }
