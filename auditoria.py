from flask import session

from database import db
from models import RegistroAuditoria, Usuario


def registrar_acao(acao, entidade, registro_id, resumo, detalhes=None):
    usuario = db.session.get(Usuario, session.get("usuario_id"))
    db.session.add(RegistroAuditoria(
        usuario=usuario.nome_usuario if usuario else "Não identificado",
        acao=acao,
        entidade=entidade,
        registro_id=registro_id,
        resumo=resumo,
        detalhes=detalhes,
    ))


def comparar_campos(objeto, campos):
    alteracoes = []
    for nome, rotulo, novo_valor in campos:
        antigo_valor = getattr(objeto, nome)
        if antigo_valor != novo_valor:
            alteracoes.append((nome, rotulo, antigo_valor, novo_valor))
    return alteracoes


def aplicar_alteracoes(objeto, alteracoes):
    for nome, _rotulo, _antigo, novo in alteracoes:
        setattr(objeto, nome, novo)


def descrever_alteracoes(alteracoes):
    def exibir(valor):
        return "vazio" if valor is None or valor == "" else str(valor)

    return "; ".join(
        f"{rotulo}: {exibir(antigo)} → {exibir(novo)}"
        for _nome, rotulo, antigo, novo in alteracoes
    )
