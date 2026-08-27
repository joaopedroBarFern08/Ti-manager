from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime

from database import db
from models import (
    Maquina,
    Atendimento,
    Peca,
    AtendimentoPeca,
    MovimentacaoEstoque
)

atendimentos_bp = Blueprint("atendimentos", __name__)


def interpretar_identificador(identificador):

    partes = identificador.strip().upper().split("-")

    if len(partes) != 3:
        return None

    patrimonio, empresa, tipo_codigo = partes

    tipos = {
        "N": "notebook",
        "D": "desktop"
    }

    tipo = tipos.get(tipo_codigo)

    if not tipo:
        return None

    return {
        "patrimonio": patrimonio,
        "empresa": empresa,
        "tipo": tipo
    }


@atendimentos_bp.route("/atendimentos")
def atendimentos():

    atendimentos = Atendimento.query.order_by(
        Atendimento.data_entrada.desc()
    ).all()

    return render_template(
        "atendimentos.html",
        atendimentos=atendimentos
    )


@atendimentos_bp.route("/atendimentos/novo", methods=["GET", "POST"])
def novo_atendimento():

    if request.method == "POST":

        identificador = request.form[
            "identificador"
        ].strip().upper()

        problema = request.form[
            "problema_relatado"
        ].strip()

        dados = interpretar_identificador(
            identificador
        )

        if not dados:
            return render_template(
                "atendimento_form.html",
                erro=(
                    "Identificador inválido. "
                    "Use o formato "
                    "000000-EMP-N ou 000000-EMP-D."
                )
            )

        maquina = Maquina.query.filter_by(
            patrimonio=dados["patrimonio"],
            empresa=dados["empresa"]
        ).first()

        if not maquina:

            maquina = Maquina(
                patrimonio=dados["patrimonio"],
                empresa=dados["empresa"],
                tipo=dados["tipo"]
            )

            db.session.add(maquina)
            db.session.flush()

        atendimento = Atendimento(
            maquina_id=maquina.id,
            problema_relatado=problema,
            status="Recebido"
        )

        db.session.add(atendimento)
        db.session.commit()

        return redirect(
            url_for("atendimentos.atendimentos")
        )

    return render_template(
        "atendimento_form.html"
    )

@atendimentos_bp.route(
    "/atendimentos/<int:id>",
    methods=["GET", "POST"]
)
def detalhe_atendimento(id):

    atendimento = db.get_or_404(
            Atendimento,
            id
        )
    
    if request.method == "POST":

        atendimento.diagnostico = request.form[
            "diagnostico"
        ].strip()

        atendimento.solucao = request.form[
            "solucao"
        ].strip()

        novo_status = request.form["status"]

        atendimento.status = novo_status

        if (
            novo_status == "Finalizado"
            and atendimento.data_saida is None
        ):
            atendimento.data_saida = datetime.now()

        elif novo_status != "Finalizado":

            atendimento.data_saida = None

        db.session.commit()

        return redirect(
            url_for(
                "atendimentos.detalhe_atendimento",
                id=atendimento.id
            )
        )

    pecas = Peca.query.order_by(
        Peca.nome
    ).all()

    return render_template(
        "atendimento_detalhe.html",
        atendimento=atendimento,
        pecas=pecas
    )


@atendimentos_bp.route(
    "/atendimentos/<int:id>/adicionar-peca",
    methods=["POST"]
)
def adicionar_peca_atendimento(id):
    atendimento = db.get_or_404(
            Atendimento,
            id
        )
    
    try:

        peca_id = int(request.form["peca_id"])
        quantidade = int(request.form["quantidade"])

    except (KeyError, ValueError):

        flash(
            "Dados da peça inválidos.",
            "error"
        )

        return redirect(
            url_for(
                "atendimentos.detalhe_atendimento",
                id=id
            )
        )

    if quantidade <= 0:

        flash(
            "A quantidade deve ser maior que zero.",
            "error"
        )

        return redirect(
            url_for(
                "atendimentos.detalhe_atendimento",
                id=id
            )
        )

    peca = db.get_or_404(
        Peca,
        peca_id
    )

    if peca.quantidade < quantidade:

        flash(
            f"Estoque insuficiente. "
            f"Disponível: {peca.quantidade}.",
            "error"
        )

        return redirect(
            url_for(
                "atendimentos.detalhe_atendimento",
                id=id
            )
        )

    # Diminui o estoque
    peca.quantidade -= quantidade

    # Registra a peça no atendimento
    item = AtendimentoPeca.query.filter_by(
        atendimento_id=atendimento.id,
        peca_id=peca.id
    ).first()

    if item:

        item.quantidade += quantidade

    else:

        item = AtendimentoPeca(
            atendimento_id=atendimento.id,
            peca_id=peca.id,
            quantidade=quantidade
        )

        db.session.add(item)

    # Registra a movimentação
    movimentacao = MovimentacaoEstoque(
        peca_id=peca.id,
        tipo="saida",
        quantidade=quantidade,
        motivo=f"Utilizada no atendimento #{atendimento.id}",
        atendimento_id=atendimento.id
    )

    db.session.add(item)
    db.session.add(movimentacao)

    db.session.commit()

    flash(
        f"{peca.nome} adicionada ao atendimento.",
        "success"
    )

    return redirect(
        url_for(
            "atendimentos.detalhe_atendimento",
            id=id
        )
    )


@atendimentos_bp.route(
    "/atendimentos/<int:id>/devolver-peca/<int:item_id>",
    methods=["POST"]
)
def devolver_peca_atendimento(id, item_id):
    atendimento = db.get_or_404(
            Atendimento,
            id
        )
    
    item = db.get_or_404(
        AtendimentoPeca,
        item_id
    )

    if item.atendimento_id != atendimento.id:

        flash(
            "Essa peça não pertence a este atendimento.",
            "error"
        )

        return redirect(
            url_for(
                "atendimentos.detalhe_atendimento",
                id=id
            )
        )

    try:

        quantidade_devolver = int(
            request.form["quantidade"]
        )

    except (KeyError, ValueError):

        flash(
            "Quantidade inválida.",
            "error"
        )

        return redirect(
            url_for(
                "atendimentos.detalhe_atendimento",
                id=id
            )
        )

    if quantidade_devolver <= 0:

        flash(
            "A quantidade deve ser maior que zero.",
            "error"
        )

        return redirect(
            url_for(
                "atendimentos.detalhe_atendimento",
                id=id
            )
        )

    if quantidade_devolver > item.quantidade:

        flash(
            f"Você só pode devolver até {item.quantidade} unidade(s).",
            "error"
        )

        return redirect(
            url_for(
                "atendimentos.detalhe_atendimento",
                id=id
            )
        )

    peca = db.get_or_404(
        Peca,
        item.peca_id
    )

    # Devolve ao estoque
    peca.quantidade += quantidade_devolver

    # Registra a movimentação
    movimentacao = MovimentacaoEstoque(
        peca_id=peca.id,
        tipo="entrada",
        quantidade=quantidade_devolver,
        motivo=f"Devolução do atendimento #{atendimento.id}",
        atendimento_id=atendimento.id
    )

    db.session.add(movimentacao)

    # Diminui a quantidade utilizada no atendimento
    item.quantidade -= quantidade_devolver

    # Se devolveu tudo, remove o registro
    if item.quantidade == 0:
        db.session.delete(item)

    db.session.commit()

    flash(
        f"{quantidade_devolver} unidade(s) de {peca.nome} "
        f"devolvida(s) ao estoque.",
        "success"
    )

    return redirect(
        url_for(
            "atendimentos.detalhe_atendimento",
            id=id
        )
    )