from db import db

class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True)
    severity = db.Column(db.String(20))
    department = db.Column(db.String(100))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    disease = db.Column(db.String(200))
