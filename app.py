from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

from shared.config import Config
from db import db
from routes import (
    path_bp,
    assignment_bp,
    network_bp,
    compare_bp,
    business_bp,
    graph_bp,   # 👈 importante
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS
    CORS(app)

    # DB
    db.init_app(app)

    # ---------- Swagger ----------
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Hospital Backend API",
            "description": "API para asignación de pacientes y comparación de algoritmos",
            "version": "1.0.0"
        },
        "basePath": "/",  # raíz
    }

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }

    Swagger(app, template=swagger_template, config=swagger_config)
    # -----------------------------

    # Crear tablas
    with app.app_context():
        from models import Patient, Hospital
        db.create_all()

    # Registrar blueprints
    app.register_blueprint(path_bp)
    app.register_blueprint(assignment_bp)
    app.register_blueprint(network_bp)
    app.register_blueprint(compare_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(graph_bp)  # 👈 registra el nuevo

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
