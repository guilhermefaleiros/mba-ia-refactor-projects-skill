import logging
from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify({"erro": str(e), "sucesso": False}), 400

    @app.errorhandler(LookupError)
    def handle_lookup_error(e):
        return jsonify({"erro": str(e), "sucesso": False}), 404

    @app.errorhandler(PermissionError)
    def handle_permission_error(e):
        return jsonify({"erro": str(e), "sucesso": False}), 401

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(Exception)
    def handle_generic_error(e):
        logger.exception("Unhandled exception: %s", e)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
