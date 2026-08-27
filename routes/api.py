from flask import Blueprint, jsonify, request
from models import Peca

api_bp = Blueprint("api", __name__)


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