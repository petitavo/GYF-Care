from db import db

class Hospital(db.Model):
    __tablename__ = "hospitals"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(200))
    department = db.Column(db.String(100))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    specialties = db.Column(db.String(500))
    capacity = db.Column(db.Integer)
