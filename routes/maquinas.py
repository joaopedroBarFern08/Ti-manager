import csv
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from database import db
from models import Maquina
from navegacao import obter_proxima_url
from auditoria import aplicar_alteracoes, comparar_campos, descrever_alteracoes, registrar_acao

maquinas_bp = Blueprint("maquinas", __name__)


@maquinas_bp.route("/maquinas")
def maquinas():

    maquinas = Maquina.query.order_by(
        Maquina.patrimonio
    ).filter_by(visivel=True).all()
    maquinas_por_status = {
        status: sum(maquina.status_maquina == status for maquina in maquinas)
        for status in ("Ativo", "Em estoque", "Inativo")
    }
    modelos = sorted({(maquina.modelo or "").strip() for maquina in maquinas if (maquina.modelo or "").strip()}, key=str.casefold)
    empresas = sorted({(maquina.empresa or "").strip() for maquina in maquinas if (maquina.empresa or "").strip()}, key=str.casefold)

    return render_template(
        "maquinas.html",
        maquinas=maquinas,
        maquinas_por_status=maquinas_por_status,
        modelos=modelos,
        empresas=empresas,
    )


@maquinas_bp.route("/maquinas/<int:id>", methods=["GET", "POST"])
def detalhe_maquina(id):

    maquina = Maquina.query.get_or_404(id)
    if not maquina.visivel:
        abort(404)

    if request.method == "POST":

        empresa = request.form.get("empresa", "").strip().upper()
        tipo = request.form.get("tipo", "")

        if not empresa or tipo not in {"notebook", "desktop"}:
            flash(
                "Preencha a empresa e selecione o tipo da máquina.",
                "error"
            )
            return redirect(url_for("maquinas.detalhe_maquina", id=id))

        status_maquina = request.form.get("status_maquina", "Ativo")
        if status_maquina not in {"Ativo", "Inativo", "Em estoque"}:
            flash("Selecione um status válido para a máquina.", "error")
            return redirect(url_for("maquinas.detalhe_maquina", id=id))

        alteracoes = comparar_campos(maquina, [
            ("empresa", "Empresa", empresa),
            ("tipo", "Tipo", tipo),
            ("modelo", "Modelo", request.form.get("modelo", "").strip()),
            ("usuario", "Usuário", request.form.get("usuario", "").strip()),
            ("setor", "Setor", request.form.get("setor", "").strip()),
            ("observacao", "Observação", request.form.get("observacao", "").strip()),
            ("status_maquina", "Status", status_maquina),
        ])
        aplicar_alteracoes(maquina, alteracoes)
        maquina.ativo = status_maquina == "Ativo"

        if alteracoes:
            registrar_acao(
                "Editou", "Máquina", maquina.id,
                f"Editou a máquina {maquina.identificador}",
                descrever_alteracoes(alteracoes),
            )

        db.session.commit()

        flash(
            "Máquina atualizada com sucesso!",
            "success"
        )

        return redirect(url_for("maquinas.maquinas"))

    return render_template(
        "detalhe_maquina.html",
        maquina=maquina
    )


@maquinas_bp.route("/maquinas/nova", methods=["GET", "POST"])
def nova_maquina():

    proximo = obter_proxima_url()

    if request.method == "POST":

        patrimonio = request.form["patrimonio"].strip()
        empresa = request.form["empresa"].strip().upper()
        tipo = request.form["tipo"]
        modelo = request.form["modelo"].strip()
        usuario = request.form["usuario"].strip()
        setor = request.form["setor"].strip()
        observacao = request.form.get("observacao", "").strip()
        status_maquina = request.form.get("status_maquina", "Ativo")

        if status_maquina not in {"Ativo", "Inativo", "Em estoque"}:
            flash("Selecione um status válido para a máquina.", "error")
            return redirect(url_for("maquinas.nova_maquina"))

        existente = Maquina.query.filter_by(patrimonio=patrimonio).first()
        if existente:
            if existente.visivel:
                flash("Este patrimônio já está no registro de máquinas.", "error")
                return redirect(url_for("maquinas.detalhe_maquina", id=existente.id))

            existente.empresa = empresa
            existente.tipo = tipo
            existente.modelo = modelo
            existente.usuario = usuario
            existente.setor = setor
            existente.observacao = observacao
            existente.status_maquina = status_maquina
            existente.ativo = status_maquina == "Ativo"
            existente.visivel = True
            registrar_acao(
                "Adicionou", "Máquina", existente.id,
                f"Adicionou a máquina {existente.identificador} ao registro operacional",
            )
            db.session.commit()
            flash("Máquina adicionada ao registro com sucesso!", "success")
            return redirect(url_for("maquinas.maquinas"))

        maquina = Maquina(
            patrimonio=patrimonio,
            empresa=empresa,
            tipo=tipo,
            modelo=modelo,
            usuario=usuario,
            setor=setor,
            observacao=observacao,
            status_maquina=status_maquina,
            ativo=status_maquina == "Ativo"
        )

        db.session.add(maquina)
        db.session.flush()

        registrar_acao(
            "Adicionou", "Máquina", maquina.id,
            f"Cadastrou a máquina {maquina.identificador}",
        )
        db.session.commit()

        return redirect(url_for("maquinas.maquinas"))

    caminho_csv = Path(__file__).resolve().parents[1] / "data" / "computadores.csv"
    patrimonios = {}
    if caminho_csv.exists():
        with caminho_csv.open(encoding="utf-8-sig", newline="") as arquivo:
            for linha in csv.DictReader(arquivo):
                partes = (linha.get("identificador") or "").strip().upper().split("-")
                if len(partes) != 3:
                    continue
                patrimonio, empresa, sigla_tipo = partes
                tipo = {"N": "notebook", "D": "desktop"}.get(sigla_tipo)
                if patrimonio and empresa and tipo:
                    patrimonios[patrimonio] = {
                        "empresa": empresa,
                        "tipo": tipo,
                        "modelo": (linha.get("modelo") or "").strip()
                    }

    patrimonios.update({
        maquina.patrimonio: {
            "empresa": maquina.empresa or "",
            "tipo": maquina.tipo or "",
            "modelo": maquina.modelo or patrimonios.get(maquina.patrimonio, {}).get("modelo", "")
        }
        for maquina in Maquina.query.filter_by(visivel=True).all()
    })

    return render_template(
        "maquina_form.html",
        proximo=proximo,
        patrimonios=patrimonios
    )


@maquinas_bp.route("/maquinas/<int:id>/excluir", methods=["POST"])
def excluir_maquina(id):
    maquina = Maquina.query.get_or_404(id)
    if maquina.visivel:
        maquina.visivel = False
        registrar_acao(
            "Excluiu", "Máquina", maquina.id,
            f"Retirou a máquina {maquina.identificador} do registro operacional",
        )
        db.session.commit()
        flash("Máquina retirada do registro. O histórico relacionado foi preservado.", "success")
    return redirect(url_for("maquinas.maquinas"))
