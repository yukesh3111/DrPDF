from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Column, Integer, String, LargeBinary, Float, DateTime
db = SQLAlchemy()
class pdf(db.Model):
    id = db.Column(Integer, primary_key=True)
    user=db.Column(String(255), nullable=False)
    filename = db.Column(String(255), nullable=False)
    documentname = db.Column(String(255), nullable=False)
    keywords = db.Column(String(500), nullable=True)
    size = db.Column(Float, nullable=False)
    datalink = db.Column(String(500), nullable=False)  
    date = db.Column(String(255), nullable=False)
    
    def __init__(self, filename, user,documentname, datalink, date, size, keywords):
        self.filename = filename
        self.user = user
        self.documentname = documentname
        self.datalink = datalink
        self.date = date
        self.size = size
        self.keywords = keywords

class recently(db.Model):
    id = db.Column(Integer, primary_key=True)
    user = db.Column(String(255))
    datalink = db.Column(String(500), nullable=False)
    created_at= db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user, datalink):
        self.user = user
        self.datalink = datalink

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
