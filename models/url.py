# models/url.py
from app import db
import datetime

class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_alias = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    clicks = db.relationship('Click', backref='url', lazy=True)