from flask import Blueprint, render_template, request, redirect, url_for, flash

from database import db
from models import MovimentacaoEstoque, Peca
from navegacao import obter_proxima_url

estoque_bp = Blueprint("estoque", __name__)
CATEGORIAS_PERMITIDAS = ("novo", "reparo", "ferramenta")


def url_formulario_peca(proximo):
    if proximo:
        return url_for("estoque.nova_peca", proximo=proximo)

    return url_for("estoque.nova_peca")


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

    proximo = obter_proxima_url()

    if request.method == "POST":
    
        nome = request.form.get("nome", "").strip()
        categoria = request.form.get("categoria", "").strip().lower()

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
                url_formulario_peca(proximo)
            )


        nome = " ".join(nome.split())
        if not nome:

            flash(
                "Informe o nome da peça.",
                "error"
            )

            return redirect(
                url_formulario_peca(proximo)
            )

        if categoria not in CATEGORIAS_PERMITIDAS:

            flash(
                "Selecione uma categoria válida.",
                "error"
            )

            return redirect(
                url_formulario_peca(proximo)
            )


        if quantidade < 0:

            flash(
                "O estoque não pode ser negativo.",
                "error"
            )

            return redirect(
                url_formulario_peca(proximo)
            )


        if estoque_minimo < 0:

            flash(
                "O estoque mínimo não pode ser negativo.",
                "error"
            )

            return redirect(
                url_formulario_peca(proximo)
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
                    url_formulario_peca(proximo)
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
                proximo or url_for("estoque.estoque")
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
                url_formulario_peca(proximo)
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
            proximo or url_for("estoque.estoque")
        )


    return render_template(
        "peca_form.html",
        proximo=proximo
    )


@estoque_bp.route("/saida", methods=["GET", "POST"])
def saida():
    if request.method == "POST":
        peca_id = request.form.get("peca_id", type=int)
        destinatario = " ".join(request.form.get("destinatario", "").split())

        try:
            quantidade = int(request.form.get("quantidade", ""))
        except (TypeError, ValueError):
            quantidade = 0

        if not peca_id:
            flash("Selecione um produto da lista de sugestões.", "error")
            return redirect(url_for("estoque.saida"))

        if not destinatario:
            flash("Informe para quem o produto foi entregue.", "error")
            return redirect(url_for("estoque.saida"))

        if quantidade <= 0:
            flash("Informe uma quantidade maior que zero.", "error")
            return redirect(url_for("estoque.saida"))

        peca = db.session.get(Peca, peca_id)

        if not peca:
            flash("Produto não encontrado.", "error")
            return redirect(url_for("estoque.saida"))

        if quantidade > peca.quantidade:
            flash(
                f"Estoque insuficiente. Disponível: {peca.quantidade} unidade(s).",
                "error"
            )
            return redirect(url_for("estoque.saida"))

        peca.quantidade -= quantidade
        db.session.add(MovimentacaoEstoque(
            peca_id=peca.id,
            tipo="saida",
            quantidade=quantidade,
            motivo="Saída avulsa",
            destinatario=destinatario,
        ))
        db.session.commit()

        flash(
            f"Saída de {quantidade} unidade(s) de {peca.nome} registrada.",
            "success"
        )
        return redirect(url_for("estoque.saida"))

    movimentacoes = MovimentacaoEstoque.query.order_by(
        MovimentacaoEstoque.data.desc()
    ).all()

    return render_template(
        "saida_form.html",
        movimentacoes=movimentacoes
    )


@estoque_bp.route("/pecas/<int:id>")
def editar_peca(id):

    peca = db.get_or_404(Peca, id)

    return render_template(
        "peca_form.html",
        peca=peca,
        proximo=None
    )
