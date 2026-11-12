from datetime import datetime
from database import db


class Maquina(db.Model):
    __tablename__ = "maquinas"

    id = db.Column(db.Integer, primary_key=True)

    patrimonio = db.Column(
        db.String(20),
        nullable=False
    )

    empresa = db.Column(
        db.String(20),
        nullable=True
    )

    tipo = db.Column(
        db.String(20),
        nullable=True
    )

    modelo = db.Column(
        db.String(100),
        nullable=True
    )

    usuario = db.Column(
        db.String(100)
    )

    setor = db.Column(
        db.String(100)
    )

    ativo = db.Column(
        db.Boolean,
        default=True
    )

    atendimentos = db.relationship(
        "Atendimento",
        backref="maquina",
        lazy=True
    )

    @property
    def identificador(self):
        if not self.empresa or not self.tipo:
            return self.patrimonio

        tipo = {
            "notebook": "N",
            "desktop": "D"
        }.get(self.tipo, self.tipo)

        return f"{self.patrimonio}-{self.empresa}-{tipo}"


class Atendimento(db.Model):
    __tablename__ = "atendimentos"

    id = db.Column(db.Integer, primary_key=True)

    maquina_id = db.Column(
        db.Integer,
        db.ForeignKey("maquinas.id"),
        nullable=False
    )

    problema_relatado = db.Column(
        db.Text,
        nullable=False
    )

    diagnostico = db.Column(db.Text)

    solucao = db.Column(db.Text)

    status = db.Column(
        db.String(50),
        default="Recebido",
        nullable=False
    )

    data_entrada = db.Column(
        db.DateTime,
        default=datetime.now,
        nullable=False
    )

    data_saida = db.Column(db.DateTime)

    pecas = db.relationship(
        "AtendimentoPeca",
        backref="atendimento",
        lazy=True
    )


class Peca(db.Model):
    __tablename__ = "pecas"
    __table_args__ = (
        db.CheckConstraint(
            "categoria IN ('novo', 'reparo', 'ferramenta')",
            name="ck_pecas_categoria_valida"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    nome = db.Column(
        db.String(100),
        nullable=False
    )

    categoria = db.Column(
        db.String(20),
        nullable=False,
        default="novo"
    )

    quantidade = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    estoque_minimo = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )

    movimentacoes = db.relationship(
        "MovimentacaoEstoque",
        backref="peca",
        lazy=True
    )


class AtendimentoPeca(db.Model):
    __tablename__ = "atendimento_pecas"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    atendimento_id = db.Column(
        db.Integer,
        db.ForeignKey("atendimentos.id"),
        nullable=False
    )

    peca_id = db.Column(
        db.Integer,
        db.ForeignKey("pecas.id"),
        nullable=False
    )

    quantidade = db.Column(
        db.Integer,
        nullable=False
    )

    peca = db.relationship(
        "Peca"
    )


class MovimentacaoEstoque(db.Model):
    __tablename__ = "movimentacoes_estoque"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    peca_id = db.Column(
        db.Integer,
        db.ForeignKey("pecas.id"),
        nullable=False
    )

    tipo = db.Column(
        db.String(20),
        nullable=False
    )

    quantidade = db.Column(
        db.Integer,
        nullable=False
    )

    motivo = db.Column(
        db.String(255)
    )

    destinatario = db.Column(
        db.String(100)
    )

    atendimento_id = db.Column(
        db.Integer,
        db.ForeignKey("atendimentos.id")
    )

    data = db.Column(
        db.DateTime,
        default=datetime.now
    )
