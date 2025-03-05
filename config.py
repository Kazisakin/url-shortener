# config.py
import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "instance", "urlshortener.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'a-very-long-and-random-secret-key-1234567890'