from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from database import db
from models import Usuario
from auditoria import registrar_acao
from routes.auth import administrador_requerido


usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/usuarios")
@administrador_requerido
def usuarios():
    contas = Usuario.query.order_by(Usuario.nome_usuario).all()
    return render_template("usuarios.html", contas=contas)


@usuarios_bp.route("/usuarios/criar", methods=["POST"])
@administrador_requerido
def criar_usuario():
    nome_usuario = request.form.get("nome_usuario", "").strip().casefold()
    senha = request.form.get("senha", "")

    if len(nome_usuario) < 3 or len(nome_usuario) > 80:
        flash("O usuário precisa ter entre 3 e 80 caracteres.", "error")
    elif len(senha) < 8:
        flash("A senha precisa ter pelo menos 8 caracteres.", "error")
    elif Usuario.query.filter_by(nome_usuario=nome_usuario).first():
        flash("Esse usuário já está cadastrado.", "error")
    else:
        usuario = Usuario(
            nome_usuario=nome_usuario,
            senha_hash=generate_password_hash(senha),
            is_admin=request.form.get("is_admin") == "on",
            is_active=True,
        )
        db.session.add(usuario)
        db.session.flush()
        registrar_acao(
            "Adicionou", "Usuário", usuario.id,
            f"Criou a conta {usuario.nome_usuario}",
        )
        db.session.commit()
        flash(f"A conta {usuario.nome_usuario} foi criada.", "success")

    return redirect(url_for("usuarios.usuarios"))


@usuarios_bp.route("/usuarios/<int:usuario_id>/acao", methods=["POST"])
@administrador_requerido
def alterar_usuario(usuario_id):
    usuario = db.get_or_404(Usuario, usuario_id)
    acao = request.form.get("acao")
    usuario_atual_id = session.get("usuario_id")

    if acao == "desativar" and usuario.id == usuario_atual_id:
        flash("Você não pode desativar sua própria conta.", "error")
    elif acao == "remover_admin" and usuario.id == usuario_atual_id:
        flash("Você não pode remover seu próprio perfil de administrador.", "error")
    elif acao in {"desativar", "remover_admin"} and usuario.is_admin and usuario.is_active:
        administradores_ativos = Usuario.query.filter_by(
            is_admin=True, is_active=True
        ).count()
        if administradores_ativos <= 1:
            flash("Mantenha ao menos um administrador ativo no sistema.", "error")
            return redirect(url_for("usuarios.usuarios"))
        if acao == "desativar":
            usuario.is_active = False
        else:
            usuario.is_admin = False
        db.session.commit()
        flash(f"As permissões de {usuario.nome_usuario} foram atualizadas.", "success")
    elif acao == "desativar":
        usuario.is_active = False
        db.session.commit()
        flash(f"A conta {usuario.nome_usuario} foi desativada.", "success")
    elif acao == "ativar":
        usuario.is_active = True
        db.session.commit()
        flash(f"A conta {usuario.nome_usuario} foi ativada.", "success")
    elif acao == "tornar_admin":
        usuario.is_admin = True
        db.session.commit()
        flash(f"{usuario.nome_usuario} agora é administrador.", "success")
    elif acao == "remover_admin":
        usuario.is_admin = False
        db.session.commit()
        flash(f"O perfil de administrador foi removido de {usuario.nome_usuario}.", "success")
    else:
        flash("Ação inválida.", "error")

    return redirect(url_for("usuarios.usuarios"))
