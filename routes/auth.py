from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models import Usuario
from auditoria import registrar_acao


auth_bp = Blueprint("auth", __name__)


def destino_local(proximo):
    if not proximo:
        return url_for("dashboard.dashboard")
    parsed = urlparse(proximo)
    if (parsed.scheme or parsed.netloc or not proximo.startswith("/")
            or proximo.startswith(("//", "/\\"))):
        return url_for("dashboard.dashboard")
    return proximo


@auth_bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    proximo = request.args.get("proximo", "")
    if request.method == "POST":
        nome_usuario = request.form.get("nome_usuario", "").strip().casefold()
        senha = request.form.get("senha", "")
        usuario = Usuario.query.filter_by(nome_usuario=nome_usuario).first()
        if usuario and check_password_hash(usuario.senha_hash, senha):
            session.clear()
            session["usuario_id"] = usuario.id
            registrar_acao("Acessou", "Sessão", None, "Entrou no TI Manager")
            db.session.commit()
            return redirect(destino_local(request.form.get("proximo", "")))
        flash("Usuário ou senha inválidos.", "error")
    return render_template("entrar.html", proximo=proximo)


@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome_usuario = request.form.get("nome_usuario", "").strip().casefold()
        senha = request.form.get("senha", "")
        confirmar = request.form.get("confirmar_senha", "")

        if len(nome_usuario) < 3 or len(nome_usuario) > 80:
            flash("O usuário precisa ter entre 3 e 80 caracteres.", "error")
        elif len(senha) < 8:
            flash("A senha precisa ter pelo menos 8 caracteres.", "error")
        elif senha != confirmar:
            flash("As senhas não são iguais.", "error")
        elif Usuario.query.filter_by(nome_usuario=nome_usuario).first():
            flash("Esse usuário já está cadastrado.", "error")
        else:
            usuario = Usuario(
                nome_usuario=nome_usuario,
                senha_hash=generate_password_hash(senha),
            )
            db.session.add(usuario)
            db.session.flush()
            session.clear()
            session["usuario_id"] = usuario.id
            registrar_acao("Adicionou", "Usuário", usuario.id, "Criou uma conta no TI Manager")
            db.session.commit()
            return redirect(url_for("dashboard.dashboard"))

    return render_template("cadastro.html")


@auth_bp.route("/sair", methods=["POST"])
def sair():
    registrar_acao("Acessou", "Sessão", None, "Saiu do TI Manager")
    db.session.commit()
    session.clear()
    return redirect(url_for("auth.entrar"))
