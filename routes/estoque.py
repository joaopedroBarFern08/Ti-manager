from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from database import db
from models import MovimentacaoEstoque, Peca, Maquina, RegistroAuditoria
from navegacao import obter_proxima_url
from auditoria import comparar_campos, descrever_alteracoes, registrar_acao

estoque_bp = Blueprint("estoque", __name__)
CATEGORIAS_PERMITIDAS = ("novo", "reparo", "ferramenta")


def url_formulario_peca(proximo):
    if proximo:
        return url_for("estoque.nova_peca", proximo=proximo)

    return url_for("estoque.nova_peca")


@estoque_bp.route("/estoque")
def estoque():

    pecas = Peca.query.filter_by(visivel=True).order_by(Peca.nome).all()
    pecas.sort(key=lambda peca: (
        0 if peca.quantidade == 0 else 1 if peca.quantidade <= peca.estoque_minimo else 2,
        peca.nome.casefold(),
    ))
    itens_estoque_baixo = sum(peca.quantidade <= peca.estoque_minimo for peca in pecas)
    itens_sem_estoque = sum(peca.quantidade == 0 for peca in pecas)
    unidades_disponiveis = sum(peca.quantidade for peca in pecas)

    return render_template(
        "estoque.html",
        pecas=pecas,
        itens_estoque_baixo=itens_estoque_baixo,
        itens_sem_estoque=itens_sem_estoque,
        unidades_disponiveis=unidades_disponiveis,
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

            if not peca or not peca.visivel:

                flash(
                    "Peça não encontrada.",
                    "error"
                )

                return redirect(
                    url_formulario_peca(proximo)
                )


            alteracoes = comparar_campos(peca, [
                ("nome", "Nome", nome),
                ("categoria", "Categoria", categoria),
                ("quantidade", "Quantidade", quantidade),
                ("estoque_minimo", "Estoque mínimo", estoque_minimo),
            ])
            for nome_campo, _rotulo, _antigo, novo_valor in alteracoes:
                setattr(peca, nome_campo, novo_valor)

            if alteracoes:
                registrar_acao(
                    "Editou", "Item do estoque", peca.id,
                    f"Editou o item {peca.nome}",
                    descrever_alteracoes(alteracoes),
                )

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

        peca_existente = Peca.query.filter_by(nome=nome, visivel=True).first()


        if peca_existente:

            flash(
                f"A peça '{peca_existente.nome}' já existe. "
                f"Selecione-a na sugestão para editar seus dados.",
                "error"
            )

            return redirect(
                url_formulario_peca(proximo)
            )

        peca_oculta = Peca.query.filter_by(nome=nome, visivel=False).first()
        if peca_oculta:
            peca_oculta.categoria = categoria
            peca_oculta.quantidade = quantidade
            peca_oculta.estoque_minimo = estoque_minimo
            peca_oculta.visivel = True
            registrar_acao(
                "Adicionou", "Item do estoque", peca_oculta.id,
                f"Reativou o item {peca_oculta.nome} no estoque",
            )
            db.session.commit()
            flash(f"Peça '{peca_oculta.nome}' adicionada novamente ao estoque.", "success")
            return redirect(proximo or url_for("estoque.estoque"))


        peca = Peca(
            nome=nome,
            categoria=categoria,
            quantidade=quantidade,
            estoque_minimo=estoque_minimo
        )

        db.session.add(peca)
        db.session.flush()
        registrar_acao(
            "Adicionou", "Item do estoque", peca.id,
            f"Cadastrou o item {peca.nome}",
            f"Categoria: {peca.categoria}; quantidade: {peca.quantidade}; mínimo: {peca.estoque_minimo}.",
        )
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
    tipo_saida = request.args.get("tipo", "estoque")
    if tipo_saida not in {"estoque", "maquina"}:
        tipo_saida = "estoque"

    if request.method == "POST":
        peca_id = request.form.get("peca_id", type=int)
        destinatario = " ".join(request.form.get("destinatario", "").split())

        try:
            quantidade = int(request.form.get("quantidade", ""))
        except (TypeError, ValueError):
            quantidade = 0

        if not peca_id:
            flash("Selecione um produto da lista de sugestões.", "error")
            return redirect(url_for("estoque.saida", tipo="estoque"))

        if not destinatario:
            flash("Informe para quem o produto foi entregue.", "error")
            return redirect(url_for("estoque.saida", tipo="estoque"))

        if quantidade <= 0:
            flash("Informe uma quantidade maior que zero.", "error")
            return redirect(url_for("estoque.saida", tipo="estoque"))

        peca = db.session.get(Peca, peca_id)

        if not peca or not peca.visivel:
            flash("Produto não encontrado.", "error")
            return redirect(url_for("estoque.saida", tipo="estoque"))

        if quantidade > peca.quantidade:
            flash(
                f"Estoque insuficiente. Disponível: {peca.quantidade} unidade(s).",
                "error"
            )
            return redirect(url_for("estoque.saida", tipo="estoque"))

        peca.quantidade -= quantidade
        db.session.add(MovimentacaoEstoque(
            peca_id=peca.id,
            tipo="saida",
            quantidade=quantidade,
            motivo="Saída avulsa",
            destinatario=destinatario,
        ))
        registrar_acao(
            "Movimentou", "Estoque", peca.id,
            f"Registrou saída de {quantidade} unidade(s) de {peca.nome}",
            f"Destinatário: {destinatario}; saldo restante: {peca.quantidade}.",
        )
        db.session.commit()

        flash(
            f"Saída de {quantidade} unidade(s) de {peca.nome} registrada.",
            "success"
        )
        return redirect(url_for("estoque.saida", tipo="estoque"))

    movimentacoes = (
        MovimentacaoEstoque.query.order_by(MovimentacaoEstoque.data.desc()).all()
        if tipo_saida == "estoque" else []
    )
    maquinas_em_estoque = (
        Maquina.query.filter_by(visivel=True, status_maquina="Em estoque")
        .order_by(Maquina.patrimonio).all()
        if tipo_saida == "maquina" else []
    )
    saidas_maquinas = (
        RegistroAuditoria.query.filter_by(entidade="Saída de máquina")
        .order_by(RegistroAuditoria.data_hora.desc(), RegistroAuditoria.id.desc())
        .limit(100).all()
        if tipo_saida == "maquina" else []
    )

    return render_template(
        "saida_form.html",
        tipo_saida=tipo_saida,
        movimentacoes=movimentacoes,
        maquinas_em_estoque=maquinas_em_estoque,
        saidas_maquinas=saidas_maquinas,
    )


@estoque_bp.route("/saida/maquina", methods=["POST"])
def saida_maquina():
    maquina_id = request.form.get("maquina_id", type=int)
    setor = " ".join(request.form.get("setor", "").split())
    usuario = " ".join(request.form.get("usuario", "").split()) or None

    if not maquina_id:
        flash("Selecione uma máquina do estoque.", "error")
        return redirect(url_for("estoque.saida", tipo="maquina"))
    if not setor:
        flash("Informe o setor de destino da máquina.", "error")
        return redirect(url_for("estoque.saida", tipo="maquina"))

    maquina = Maquina.query.filter_by(
        id=maquina_id,
        visivel=True,
        status_maquina="Em estoque",
    ).first()
    if not maquina:
        flash("A máquina selecionada não está mais disponível em estoque.", "error")
        return redirect(url_for("estoque.saida", tipo="maquina"))

    maquina.status_maquina = "Ativo"
    maquina.ativo = True
    maquina.setor = setor
    maquina.usuario = usuario
    registrar_acao(
        "Movimentou", "Saída de máquina", maquina.id,
        f"Entregou a máquina {maquina.identificador}",
        f"Setor: {setor}; usuário: {usuario or 'não informado'}.",
    )
    db.session.commit()

    flash(f"Máquina {maquina.identificador} entregue ao setor {setor}.", "success")
    return redirect(url_for("estoque.saida", tipo="maquina"))


@estoque_bp.route("/pecas/<int:id>")
def editar_peca(id):

    peca = db.get_or_404(Peca, id)
    if not peca.visivel:
        abort(404)

    return render_template(
        "peca_form.html",
        peca=peca,
        proximo=None
    )


@estoque_bp.route("/pecas/<int:id>/excluir", methods=["POST"])
def excluir_peca(id):
    peca = db.get_or_404(Peca, id)
    if peca.visivel:
        peca.visivel = False
        registrar_acao(
            "Excluiu", "Item do estoque", peca.id,
            f"Retirou o item {peca.nome} do estoque",
            f"Saldo registrado no momento da retirada: {peca.quantidade}.",
        )
        db.session.commit()
        flash("Item retirado do estoque. O histórico de movimentações foi preservado.", "success")
    return redirect(url_for("estoque.estoque"))
