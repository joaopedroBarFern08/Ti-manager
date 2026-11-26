from flask import Blueprint, render_template, request, session
from sqlalchemy import desc

from database import db
from models import RegistroAuditoria, Usuario


relatorios_bp = Blueprint("relatorios", __name__)


@relatorios_bp.route("/relatorios")
def relatorios():
    page = request.args.get("pagina", 1, type=int)
    usuario = db.session.get(Usuario, session.get("usuario_id"))
    consulta = RegistroAuditoria.query
    if not usuario or not usuario.is_admin:
        consulta = consulta.filter(RegistroAuditoria.acao != "Acessou")

    paginacao = consulta.order_by(
        desc(RegistroAuditoria.data_hora), desc(RegistroAuditoria.id)
    ).paginate(page=max(page, 1), per_page=50, error_out=False)
    return render_template(
        "relatorios.html",
        paginacao=paginacao,
        administrador=bool(usuario and usuario.is_admin),
    )
