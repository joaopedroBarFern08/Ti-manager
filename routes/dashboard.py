from flask import Blueprint, render_template
from models import Maquina, Atendimento, Peca

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def dashboard():

    total_maquinas = Maquina.query.filter_by(ativo=True).count()

    total_atendimentos = Atendimento.query.count()

    atendimentos_abertos = Atendimento.query.filter(
        Atendimento.status != "Finalizado"
    ).count()

    pecas = Peca.query.all()

    estoque_baixo = [
        peca for peca in pecas
        if peca.quantidade <= peca.estoque_minimo
    ]

    return render_template(
        "dashboard.html",
        total_maquinas=total_maquinas,
        total_atendimentos=total_atendimentos,
        atendimentos_abertos=atendimentos_abertos,
        estoque_baixo=estoque_baixo
    )