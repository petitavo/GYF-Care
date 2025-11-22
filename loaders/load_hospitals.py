import os
import pandas as pd
from app import create_app
from db import db
from models import Hospital

# Obtiene la carpeta raíz del proyecto: C:\Users\tavo1\hospital-backend
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Ruta correcta del CSV
HOSPITALS_FILE = os.path.join(BASE_DIR, "data", "hospitalesprueba.csv")

app = create_app()

with app.app_context():
    print(f"Cargando hospitales desde: {HOSPITALS_FILE}")

    df = pd.read_csv(HOSPITALS_FILE)

    print("Cargando hospitales en MySQL...")

    for _, row in df.iterrows():
        h = Hospital(
            code=row["ID_Hospital"],
            name=row["Nombre"],
            department=row["Departamento"],
            lat=float(row["Latitud"]),
            lon=float(row["Longitud"]),
            specialties=row.get("Especialidades", ""),
            capacity=int(row.get("Capacidad", 0)),
        )
        db.session.add(h)

    db.session.commit()

    print("✔️ Se cargaron todos los hospitales correctamente.")
