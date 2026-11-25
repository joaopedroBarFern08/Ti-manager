from flask import Blueprint, render_template, request
from sqlalchemy import desc

from models import RegistroAuditoria


relatorios_bp = Blueprint("relatorios", __name__)


@relatorios_bp.route("/relatorios")
def relatorios():
    page = request.args.get("pagina", 1, type=int)
    paginacao = RegistroAuditoria.query.order_by(
        desc(RegistroAuditoria.data_hora), desc(RegistroAuditoria.id)
    ).paginate(page=max(page, 1), per_page=50, error_out=False)
    return render_template("relatorios.html", paginacao=paginacao)
