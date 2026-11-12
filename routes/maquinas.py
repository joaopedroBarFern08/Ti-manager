from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import db
from models import Maquina
from navegacao import obter_proxima_url

maquinas_bp = Blueprint("maquinas", __name__)


@maquinas_bp.route("/maquinas")
def maquinas():

    maquinas = Maquina.query.order_by(
        Maquina.patrimonio
    ).all()

    return render_template(
        "maquinas.html",
        maquinas=maquinas
    )


@maquinas_bp.route("/maquinas/<int:id>", methods=["GET", "POST"])
def detalhe_maquina(id):

    maquina = Maquina.query.get_or_404(id)

    if request.method == "POST":

        empresa = request.form.get("empresa", "").strip().upper()
        tipo = request.form.get("tipo", "")

        if not empresa or tipo not in {"notebook", "desktop"}:
            flash(
                "Preencha a empresa e selecione o tipo da máquina.",
                "error"
            )
            return redirect(url_for("maquinas.detalhe_maquina", id=id))

        maquina.empresa = empresa
        maquina.tipo = tipo

        maquina.modelo = request.form.get(
            "modelo", ""
        ).strip()

        maquina.usuario = request.form.get(
            "usuario", ""
        ).strip()

        maquina.setor = request.form.get(
            "setor", ""
        ).strip()

        valor_ativo = request.form.get("ativo")

        maquina.ativo = valor_ativo == "1"

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

        maquina = Maquina(
            patrimonio=patrimonio,
            empresa=empresa,
            tipo=tipo,
            modelo=modelo,
            usuario=usuario,
            setor=setor
        )

        db.session.add(maquina)
        db.session.commit()

        return redirect(url_for("maquinas.maquinas"))

    return render_template("maquina_form.html", proximo=proximo)
