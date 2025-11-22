import os
import pandas as pd
from app import create_app
from db import db
from models import Patient

# Obtiene la carpeta raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Ruta correcta del CSV
PATIENTS_FILE = os.path.join(BASE_DIR, "data", "pacientes.csv")

app = create_app()

with app.app_context():
    print(f"Cargando pacientes desde: {PATIENTS_FILE}")

    df = pd.read_csv(PATIENTS_FILE)

    print("Cargando pacientes en MySQL...")

    for _, row in df.iterrows():
        p = Patient(
            code=row["ID_Paciente"],
            severity=row["Gravedad"],
            department=row["Departamento"],
            lat=float(row["Latitud"]),
            lon=float(row["Longitud"]),
            disease=row["Enfermedad"],
        )
        db.session.add(p)

    db.session.commit()

    print("✔️ Se cargaron todos los pacientes correctamente.")
