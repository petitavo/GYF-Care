# app.py
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
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS
    CORS(app)

    # DB
    db.init_app(app)

    # Swagger configuración básica
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
                "rule_filter": lambda rule: True,  # incluir todas las rutas
                "model_filter": lambda tag: True,  # incluir todos los modelos
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"  # aquí estará la UI
    }

    Swagger(app, template=swagger_template, config=swagger_config)

    # Crear tablas
    with app.app_context():
        from models import Patient, Hospital  # asegura que los modelos se registren
        db.create_all()

    # Register blueprints
    app.register_blueprint(path_bp)
    app.register_blueprint(assignment_bp)
    app.register_blueprint(network_bp)
    app.register_blueprint(compare_bp)
    app.register_blueprint(business_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
