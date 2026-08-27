from flask import Flask
from database import db
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

from models import *

from routes.dashboard import dashboard_bp
from routes.maquinas import maquinas_bp
from routes.atendimentos import atendimentos_bp
from routes.estoque import estoque_bp
from routes.api import api_bp

app.register_blueprint(dashboard_bp)
app.register_blueprint(maquinas_bp)
app.register_blueprint(atendimentos_bp)
app.register_blueprint(estoque_bp)
app.register_blueprint(api_bp)


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)