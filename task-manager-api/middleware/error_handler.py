import logging

from flask import jsonify

from utils.errors import ForbiddenError, NotFoundError, UnauthorizedError, ValidationError


logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({"erro": str(error), "sucesso": False}), error.status_code

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        return jsonify({"erro": str(error), "sucesso": False}), error.status_code

    @app.errorhandler(UnauthorizedError)
    def handle_unauthorized_error(error):
        return jsonify({"erro": str(error), "sucesso": False}), error.status_code

    @app.errorhandler(ForbiddenError)
    def handle_forbidden_error(error):
        return jsonify({"erro": str(error), "sucesso": False}), error.status_code

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        return jsonify({"erro": str(error), "sucesso": False}), 400

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Unhandled exception")
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
