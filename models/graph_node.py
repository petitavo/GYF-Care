from db import db

class GraphNode(db.Model):
    __tablename__ = "graph_nodes"

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(20))   # patient / hospital
    entity_id = db.Column(db.Integer)        # FK a patient u hospital
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
