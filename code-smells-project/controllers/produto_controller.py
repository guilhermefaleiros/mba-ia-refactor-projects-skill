import logging
import models.produto as produto_model

logger = logging.getLogger(__name__)

CATEGORIAS_VALIDAS = {"informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"}
NOME_MIN_LEN = 2
NOME_MAX_LEN = 200


def listar():
    produtos = produto_model.get_todos()
    logger.info("Listing %d products", len(produtos))
    return produtos


def buscar_por_id(id):
    produto = produto_model.get_por_id(id)
    if produto is None:
        raise LookupError("Produto não encontrado")
    return produto


def buscar(termo=None, categoria=None, preco_min=None, preco_max=None):
    return produto_model.buscar(termo, categoria, preco_min, preco_max)


def criar(dados):
    _validar(dados)
    id = produto_model.criar(
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    logger.info("Product created with id: %d", id)
    return {"id": id}


def atualizar(id, dados):
    if produto_model.get_por_id(id) is None:
        raise LookupError("Produto não encontrado")
    _validar(dados)
    produto_model.atualizar(
        id,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )


def deletar(id):
    if produto_model.get_por_id(id) is None:
        raise LookupError("Produto não encontrado")
    produto_model.deletar(id)
    logger.info("Product %d deleted", id)


def _validar(dados):
    if not dados:
        raise ValueError("Dados inválidos")
    for campo in ("nome", "preco", "estoque"):
        if campo not in dados:
            raise ValueError(f"{campo.capitalize()} é obrigatório")
    nome = dados["nome"]
    if len(nome) < NOME_MIN_LEN:
        raise ValueError("Nome muito curto")
    if len(nome) > NOME_MAX_LEN:
        raise ValueError("Nome muito longo")
    if dados["preco"] < 0:
        raise ValueError("Preço não pode ser negativo")
    if dados["estoque"] < 0:
        raise ValueError("Estoque não pode ser negativo")
    categoria = dados.get("categoria", "geral")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoria inválida. Válidas: {sorted(CATEGORIAS_VALIDAS)}")
