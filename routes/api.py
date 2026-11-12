from flask import Blueprint, jsonify, request
from models import Peca
import unicodedata

api_bp = Blueprint("api", __name__)


def chave_busca(texto):
    texto_normalizado = unicodedata.normalize(
        "NFD",
        " ".join(texto.split()).casefold()
    )

    return "".join(
        caractere
        for caractere in texto_normalizado
        if unicodedata.category(caractere) != "Mn"
    )


@api_bp.route("/api/pecas")
def api_pecas():

    pecas = Peca.query.order_by(
        Peca.nome
    ).all()

    return jsonify([
        {
            "id": peca.id,
            "nome": peca.nome,
            "quantidade": peca.quantidade
        }
        for peca in pecas
    ])


@api_bp.route("/api/pecas/<int:id>")
def dados_peca(id):

    peca = Peca.query.get_or_404(id)

    return jsonify({
        "id": peca.id,
        "nome": peca.nome,
        "categoria": peca.categoria or "",
        "quantidade": peca.quantidade,
        "estoque_minimo": peca.estoque_minimo
    })


@api_bp.route("/api/pecas/buscar")
def buscar_pecas():

    termo = request.args.get(
        "q", ""
    ).strip()

    if not termo:
        return jsonify([])

    pecas = Peca.query.filter(
        Peca.nome.ilike(f"%{termo}%")
    ).order_by(
        Peca.nome
    ).limit(10).all()

    return jsonify([
        {
            "id": peca.id,
            "nome": peca.nome,
            "categoria": peca.categoria or "",
            "quantidade": peca.quantidade,
            "estoque_minimo": peca.estoque_minimo
        }
        for peca in pecas
    ])


@api_bp.route("/api/categorias/buscar")
def buscar_categorias():

    termo = request.args.get("q", "").strip()

    if not termo:
        return jsonify([])

    chave_termo = chave_busca(termo)
    categorias = Peca.query.with_entities(Peca.categoria).filter(
        Peca.categoria.isnot(None),
        Peca.categoria != ""
    ).all()

    resultados = []
    chaves_encontradas = set()

    for categoria, in categorias:
        chave_categoria = chave_busca(categoria)

        if (
            chave_termo in chave_categoria
            and chave_categoria not in chaves_encontradas
        ):
            resultados.append(categoria)
            chaves_encontradas.add(chave_categoria)

    return jsonify(sorted(resultados, key=str.casefold)[:10])
