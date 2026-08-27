from flask import Blueprint, render_template, request, redirect, url_for, flash

from database import db
from models import Peca

estoque_bp = Blueprint("estoque", __name__)


@estoque_bp.route("/estoque")
def estoque():

    pecas = Peca.query.order_by(
        Peca.nome
    ).all()

    return render_template(
        "estoque.html",
        pecas=pecas
    )


@estoque_bp.route("/pecas/nova", methods=["GET", "POST"])
def nova_peca():

    if request.method == "POST":
    
        nome = request.form.get("nome", "").strip()
        categoria = request.form.get("categoria", "").strip()

        peca_id = request.form.get("peca_id")

        try:
            quantidade = int(
                request.form.get("quantidade", 0)
            )

            estoque_minimo = int(
                request.form.get("estoque_minimo", 1)
            )

        except (ValueError, TypeError):

            flash(
                "Informe valores numéricos válidos.",
                "error"
            )

            return redirect(
                url_for("estoque.nova_peca")
            )


        nome = " ".join(nome.split())
        categoria = " ".join(categoria.split())


        if not nome:

            flash(
                "Informe o nome da peça.",
                "error"
            )

            return redirect(
                url_for("estoque.nova_peca")
            )


        if quantidade < 0:

            flash(
                "O estoque não pode ser negativo.",
                "error"
            )

            return redirect(
                url_for("estoque.nova_peca")
            )


        if estoque_minimo < 0:

            flash(
                "O estoque mínimo não pode ser negativo.",
                "error"
            )

            return redirect(
                url_for("estoque.nova_peca")
            )


        # =================================
        # EDITANDO PEÇA EXISTENTE
        # =================================

        if peca_id:

            peca = Peca.query.get(
                int(peca_id)
            )

            if not peca:

                flash(
                    "Peça não encontrada.",
                    "error"
                )

                return redirect(
                    url_for("estoque.nova_peca")
                )


            peca.nome = nome
            peca.categoria = categoria
            peca.quantidade = quantidade
            peca.estoque_minimo = estoque_minimo

            db.session.commit()


            flash(
                f"Peça '{peca.nome}' atualizada com sucesso.",
                "success"
            )

            return redirect(
                url_for("estoque.estoque")
            )


        # =================================
        # NOVA PEÇA
        # =================================

        peca_existente = Peca.query.filter_by(
            nome=nome
        ).first()


        if peca_existente:

            flash(
                f"A peça '{peca_existente.nome}' já existe. "
                f"Selecione-a na sugestão para editar seus dados.",
                "error"
            )

            return redirect(
                url_for("estoque.nova_peca")
            )


        peca = Peca(
            nome=nome,
            categoria=categoria,
            quantidade=quantidade,
            estoque_minimo=estoque_minimo
        )

        db.session.add(peca)

        db.session.commit()


        flash(
            f"Peça '{peca.nome}' cadastrada com sucesso.",
            "success"
        )


        return redirect(
            url_for("estoque.estoque")
        )


    return render_template(
        "peca_form.html"
    )
