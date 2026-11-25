from flask import Flask, redirect, request, session, url_for
from database import db
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

secret_key = os.getenv("SECRET_KEY")

if not secret_key or secret_key in {
    "debug-debug",
    "troque-por-uma-chave-secreta-segura"
}:
    raise RuntimeError(
        "Defina uma SECRET_KEY segura no arquivo .env ou nas variáveis de ambiente."
    )

app.config["SECRET_KEY"] = secret_key
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///ti_manager.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

from models import *

from routes.dashboard import dashboard_bp
from routes.maquinas import maquinas_bp
from routes.atendimentos import atendimentos_bp
from routes.estoque import estoque_bp
from routes.api import api_bp
from routes.auth import auth_bp
from routes.relatorios import relatorios_bp
from migrations import (
    adicionar_destinatario_movimentacao_estoque,
    adicionar_observacao_maquina,
    migrar_campos_visibilidade_maquina,
    permitir_maquina_sem_empresa_e_tipo,
    migrar_categorias_pecas,
    adicionar_visibilidade_operacional,
)

app.register_blueprint(dashboard_bp)
app.register_blueprint(maquinas_bp)
app.register_blueprint(atendimentos_bp)
app.register_blueprint(estoque_bp)
app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(relatorios_bp)


@app.before_request
def exigir_login():
    endpoints_publicos = {"auth.entrar", "auth.cadastro", "static"}
    if request.endpoint not in endpoints_publicos and not session.get("usuario_id"):
        return redirect(url_for("auth.entrar", proximo=request.full_path))


@app.context_processor
def usuario_atual_contexto():
    from models import Usuario

    usuario_id = session.get("usuario_id")
    usuario = db.session.get(Usuario, usuario_id) if usuario_id else None
    return {"usuario_atual": usuario}


with app.app_context():
    db.create_all()
    permitir_maquina_sem_empresa_e_tipo()
    migrar_categorias_pecas()
    adicionar_destinatario_movimentacao_estoque()
    adicionar_observacao_maquina()
    migrar_campos_visibilidade_maquina()
    adicionar_visibilidade_operacional()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=False
    )
