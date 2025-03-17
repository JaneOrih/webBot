from flask import Flask
from .routes import bp as chat_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(chat_bp)
    return app