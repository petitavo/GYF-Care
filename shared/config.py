import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+mysqlconnector://petitavo:tarado123.@credisas.mysql.database.azure.com/hospital_project"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Parámetros para Graph KNN
    K_NEIGHBORS = 10
