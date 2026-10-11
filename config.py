import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'health-reminder-super-secret-key-2026')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE = os.path.join(BASE_DIR, 'health_app.db')
    DEBUG = True
