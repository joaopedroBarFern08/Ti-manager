from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from datetime import datetime
import csv
from pathlib import Path

from database import db
from navegacao import obter_proxima_url
from models import (
    Maquina,
    Atendimento,
    Peca,
    AtendimentoPeca,
    MovimentacaoEstoque
)
from auditoria import comparar_campos, descrever_alteracoes, registrar_acao

atendimentos_bp = Blueprint("atendimentos", __name__)


@atendimentos_bp.route("/atendimentos")
def atendimentos():

    atendimentos = Atendimento.query.filter_by(visivel=True).order_by(
        Atendimento.data_entrada.desc()
    ).all()

    return render_template(
        "atendimentos.html",
        atendimentos=atendimentos
    )


@atendimentos_bp.route("/atendimentos/novo", methods=["GET", "POST"])
def novo_atendimento():

    proximo = obter_proxima_url()

    # Dados conhecidos permitem completar o identificador no formulário.
    caminho_csv = Path(__file__).resolve().parents[1] / "data" / "computadores.csv"
    patrimonios = {}
    if caminho_csv.exists():
        with caminho_csv.open(encoding="utf-8-sig", newline="") as arquivo:
            for linha in csv.DictReader(arquivo):
                partes = (linha.get("identificador") or "").strip().upper().split("-")
                if len(partes) == 3 and partes[0] and partes[1] and partes[2] in {"N", "D"}:
                    patrimonios[partes[0]] = f"{partes[0]}-{partes[1]}-{partes[2]}"

    for maquina_cadastrada in Maquina.query.filter_by(visivel=True).all():
        if maquina_cadastrada.empresa and maquina_cadastrada.tipo:
            patrimonios[maquina_cadastrada.patrimonio] = maquina_cadastrada.identificador

    if request.method == "POST":

        patrimonio_digitado = request.form["patrimonio"].strip().upper()
        partes_identificador = patrimonio_digitado.split("-")
        if (
            len(partes_identificador) == 3
            and partes_identificador[2] in {"N", "D"}
            and patrimonios.get(partes_identificador[0]) == patrimonio_digitado
        ):
            patrimonio = partes_identificador[0]
            empresa = partes_identificador[1]
            tipo = {"N": "notebook", "D": "desktop"}[partes_identificador[2]]
        else:
            patrimonio = patrimonio_digitado
            empresa = tipo = None

        problema = request.form[
            "problema_relatado"
        ].strip()

        if not patrimonio:
            return render_template(
                "atendimento_form.html",
                erro="Informe o patrimônio da máquina.",
                proximo=proximo,
                patrimonios=patrimonios
            )

        maquina = Maquina.query.filter_by(patrimonio=patrimonio).first()

        if not maquina:

            maquina = Maquina(
                patrimonio=patrimonio,
                empresa=empresa,
                tipo=tipo
            )

            db.session.add(maquina)
            db.session.flush()
            registrar_acao(
                "Adicionou", "Máquina", maquina.id,
                f"Criou o cadastro inicial da máquina {maquina.identificador} ao abrir atendimento",
            )
        elif not maquina.visivel:
            maquina.visivel = True
            registrar_acao(
                "Adicionou", "Máquina", maquina.id,
                f"Reativou a máquina {maquina.identificador} ao abrir atendimento",
            )

        if maquina and empresa and tipo and (not maquina.empresa or not maquina.tipo):
            maquina.empresa = empresa
            maquina.tipo = tipo

        atendimento = Atendimento(
            maquina_id=maquina.id,
            problema_relatado=problema,
            status="Recebido"
        )

        db.session.add(atendimento)
        db.session.flush()
        registrar_acao(
            "Adicionou", "Atendimento", atendimento.id,
            f"Abriu atendimento #{atendimento.id} para {maquina.identificador}",
            f"Problema relatado: {problema[:180]}",
        )
        db.session.commit()

        return redirect(
            url_for("atendimentos.atendimentos")
        )

    return render_template(
        "atendimento_form.html",
        proximo=proximo,
        patrimonios=patrimonios
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

    if not atendimento.visivel:
        abort(404)
    
    if request.method == "POST":
        novo_status = request.form["status"]
        if novo_status not in {"Recebido", "Em diagnóstico", "Aguardando peça", "Em manutenção", "Finalizado"}:
            flash("Selecione um status válido para o atendimento.", "error")
            return redirect(url_for("atendimentos.detalhe_atendimento", id=id))
        alteracoes = comparar_campos(atendimento, [
            ("diagnostico", "Diagnóstico", request.form.get("diagnostico", "").strip()),
            ("solucao", "Solução", request.form.get("solucao", "").strip()),
            ("status", "Status", novo_status),
        ])
        for nome, _rotulo, _antigo, novo_valor in alteracoes:
            setattr(atendimento, nome, novo_valor)

        if (
            novo_status == "Finalizado"
            and atendimento.data_saida is None
        ):
            atendimento.data_saida = datetime.now()

        elif novo_status != "Finalizado":

            atendimento.data_saida = None

        if alteracoes:
            registrar_acao(
                "Editou", "Atendimento", atendimento.id,
                f"Editou o atendimento #{atendimento.id}",
                descrever_alteracoes(alteracoes),
            )

        db.session.commit()

        return redirect(
            url_for(
                "atendimentos.detalhe_atendimento",
                id=atendimento.id
            )
        )

    pecas = Peca.query.filter_by(
        categoria="reparo",
        visivel=True
    ).order_by(
        Peca.nome
    ).all()

    return render_template(
        "atendimento_detalhe.html",
        atendimento=atendimento,
        pecas=pecas
    )


@atendimentos_bp.route("/atendimentos/<int:id>/excluir", methods=["POST"])
def excluir_atendimento(id):
    atendimento = db.get_or_404(Atendimento, id)
    if atendimento.visivel:
        atendimento.visivel = False
        registrar_acao(
            "Excluiu", "Atendimento", atendimento.id,
            f"Retirou o atendimento #{atendimento.id} do registro operacional",
            "O histórico e as movimentações vinculadas foram preservados.",
        )
        db.session.commit()
        flash("Atendimento retirado da lista. O histórico foi preservado.", "success")
    return redirect(url_for("atendimentos.atendimentos"))


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

    if peca.categoria != "reparo":

        flash(
            "Somente peças da categoria Reparo podem ser usadas em atendimentos.",
            "error"
        )

        return redirect(
            url_for(
                "atendimentos.detalhe_atendimento",
                id=id
            )
        )

    if not peca.visivel:
        flash("Este item foi retirado do estoque.", "error")
        return redirect(url_for("atendimentos.detalhe_atendimento", id=id))

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
    registrar_acao(
        "Adicionou", "Peça no atendimento", atendimento.id,
        f"Vinculou {quantidade} unidade(s) de {peca.nome} ao atendimento #{atendimento.id}",
        f"Estoque restante: {peca.quantidade}.",
    )

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

    registrar_acao(
        "Movimentou", "Estoque", peca.id,
        f"Devolveu {quantidade_devolver} unidade(s) de {peca.nome} do atendimento #{atendimento.id}",
        f"Saldo após devolução: {peca.quantidade}.",
    )

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
