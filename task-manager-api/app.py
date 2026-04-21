import logging

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from config import get_config
from database import db
from middleware.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from utils.time import utcnow


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.update(get_config())

    logging.basicConfig(
        level=getattr(logging, app.config["LOG_LEVEL"], logging.INFO),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    CORS(app)
    db.init_app(app)
    register_error_handlers(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(category_bp)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "timestamp": utcnow().isoformat()}), 200

    @app.route("/")
    def index():
        return jsonify({"message": "Task Manager API", "version": "2.0"}), 200

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=app.config["PORT"])
