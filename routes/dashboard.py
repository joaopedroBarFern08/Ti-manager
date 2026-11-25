from flask import Blueprint, render_template
from models import Maquina, Atendimento, Peca
from sqlalchemy import func
from database import db

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def dashboard():

    total_maquinas = Maquina.query.filter_by(status_maquina="Ativo", visivel=True).count()

    maquinas_em_estoque = Maquina.query.filter_by(
        status_maquina="Em estoque",
        visivel=True
    ).count()

    total_atendimentos = Atendimento.query.filter_by(visivel=True).count()

    atendimentos_abertos = Atendimento.query.filter(
        Atendimento.status != "Finalizado"
    ).filter_by(visivel=True).count()

    pecas = Peca.query.filter_by(visivel=True).all()

    estoque_baixo = [
        peca for peca in pecas
        if peca.quantidade <= peca.estoque_minimo
    ]

    contagem_modelos = db.session.query(
        Maquina.modelo,
        Maquina.status_maquina,
        func.count(Maquina.id)
    ).filter(
        Maquina.visivel.is_(True),
        Maquina.status_maquina.in_(["Ativo", "Em estoque"])
    ).group_by(
        Maquina.modelo,
        Maquina.status_maquina
    ).all()

    modelos = {}
    for modelo, status, quantidade in contagem_modelos:
        nome_modelo = (modelo or "").strip() or "Não informado"
        modelos.setdefault(nome_modelo, {"ativo": 0, "estoque": 0})
        chave = "ativo" if status == "Ativo" else "estoque"
        modelos[nome_modelo][chave] += quantidade

    modelos_maquinas = [
        {"nome": nome, **contagens}
        for nome, contagens in sorted(
            modelos.items(), key=lambda item: item[0].casefold()
        )
    ]
    maior_quantidade_modelo = max(
        (max(item["ativo"], item["estoque"]) for item in modelos_maquinas),
        default=0
    )

    return render_template(
        "dashboard.html",
        total_maquinas=total_maquinas,
        maquinas_em_estoque=maquinas_em_estoque,
        total_atendimentos=total_atendimentos,
        atendimentos_abertos=atendimentos_abertos,
        estoque_baixo=estoque_baixo,
        modelos_maquinas=modelos_maquinas,
        maior_quantidade_modelo=maior_quantidade_modelo
    )
