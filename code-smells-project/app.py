import logging
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from models.database import get_db
from routes.produto_routes import produto_bp
from routes.usuario_routes import usuario_bp
from routes.pedido_routes import pedido_bp
from middleware.error_handler import register_error_handlers

Config.configure_logging()

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = Config.SECRET_KEY
app.config["DEBUG"] = Config.DEBUG

CORS(app)
register_error_handlers(app)

app.register_blueprint(produto_bp)
app.register_blueprint(usuario_bp)
app.register_blueprint(pedido_bp)


@app.route("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


if __name__ == "__main__":
    Config.validate()
    get_db()
    logger.info("=" * 50)
    logger.info("SERVER STARTED")
    logger.info("Running at http://localhost:%d", Config.PORT)
    logger.info("=" * 50)
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
