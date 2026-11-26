"""Pequenas migrações de compatibilidade para o banco SQLite local."""

import csv
from pathlib import Path

from database import db


def adicionar_permissao_admin_usuario():
    """Adiciona a permissão administrativa às contas existentes."""
    conexao = db.engine.raw_connection()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'usuarios'"
        )
        if not cursor.fetchone():
            return

        cursor.execute("PRAGMA table_info(usuarios)")
        colunas = {coluna[1] for coluna in cursor.fetchall()}
        if "is_admin" not in colunas:
            cursor.execute(
                "ALTER TABLE usuarios ADD COLUMN is_admin "
                "BOOLEAN NOT NULL DEFAULT 0"
            )
            conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()


def adicionar_status_ativo_usuario():
    """Adiciona o estado ativo/inativo às contas existentes."""
    conexao = db.engine.raw_connection()
    cursor = conexao.cursor()
    try:
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'usuarios'"
        )
        if not cursor.fetchone():
            return

        cursor.execute("PRAGMA table_info(usuarios)")
        colunas = {coluna[1] for coluna in cursor.fetchall()}
        if "is_active" not in colunas:
            cursor.execute(
                "ALTER TABLE usuarios ADD COLUMN is_active "
                "BOOLEAN NOT NULL DEFAULT 1"
            )
            conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()


def adicionar_observacao_maquina():
    """Adiciona observações às máquinas já cadastradas."""
    conexao = db.engine.raw_connection()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'maquinas'"
        )

        if not cursor.fetchone():
            return

        cursor.execute("PRAGMA table_info(maquinas)")
        colunas = {coluna[1] for coluna in cursor.fetchall()}

        if "observacao" not in colunas:
            cursor.execute(
                "ALTER TABLE maquinas ADD COLUMN observacao TEXT"
            )
            conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()


def adicionar_destinatario_movimentacao_estoque():
    """Adiciona o destinatário às baixas de estoque já existentes."""
    conexao = db.engine.raw_connection()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'movimentacoes_estoque'"
        )

        if not cursor.fetchone():
            return

        cursor.execute("PRAGMA table_info(movimentacoes_estoque)")
        colunas = {coluna[1] for coluna in cursor.fetchall()}

        if "destinatario" not in colunas:
            cursor.execute(
                "ALTER TABLE movimentacoes_estoque "
                "ADD COLUMN destinatario VARCHAR(100)"
            )
            conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()


def migrar_categorias_pecas():
    """Restringe as categorias do estoque e normaliza os registros existentes."""
    conexao = db.engine.raw_connection()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = 'pecas'"
        )
        resultado = cursor.fetchone()

        if not resultado:
            return

        definicao_tabela = resultado[0] or ""
        if "ck_pecas_categoria_valida" in definicao_tabela:
            return

        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("BEGIN")
        cursor.execute(
            """
            CREATE TABLE pecas_nova (
                id INTEGER NOT NULL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                categoria VARCHAR(20) NOT NULL DEFAULT 'novo'
                    CONSTRAINT ck_pecas_categoria_valida
                    CHECK (categoria IN ('novo', 'reparo', 'ferramenta')),
                quantidade INTEGER NOT NULL DEFAULT 0,
                estoque_minimo INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO pecas_nova (id, nome, categoria, quantidade, estoque_minimo)
            SELECT id, nome, 'novo', quantidade, estoque_minimo
            FROM pecas
            """
        )
        cursor.execute("DROP TABLE pecas")
        cursor.execute("ALTER TABLE pecas_nova RENAME TO pecas")
        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()
        conexao.close()


def permitir_maquina_sem_empresa_e_tipo():
    """Permite cadastrar atendimento antes de completar a máquina.

    Versões anteriores criavam ``empresa`` e ``tipo`` como obrigatórios. O
    SQLite não permite remover esse requisito com ``ALTER TABLE``; por isso a
    tabela é recriada somente quando o banco ainda usa o formato antigo.
    """
    conexao = db.engine.raw_connection()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'maquinas'"
        )

        if not cursor.fetchone():
            return

        cursor.execute("PRAGMA table_info(maquinas)")
        colunas = {coluna[1]: coluna for coluna in cursor.fetchall()}

        empresa_obrigatoria = colunas["empresa"][3] == 1
        tipo_obrigatorio = colunas["tipo"][3] == 1

        if not empresa_obrigatoria and not tipo_obrigatorio:
            return

        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("BEGIN")
        cursor.execute(
            """
            CREATE TABLE maquinas_nova (
                id INTEGER NOT NULL PRIMARY KEY,
                patrimonio VARCHAR(20) NOT NULL,
                empresa VARCHAR(20),
                tipo VARCHAR(20),
                modelo VARCHAR(100),
                usuario VARCHAR(100),
                setor VARCHAR(100),
                ativo BOOLEAN,
                observacao TEXT,
                status_maquina VARCHAR(20) NOT NULL DEFAULT 'Ativo'
            )
            """
        )
        observacao_origem = "observacao" if "observacao" in colunas else "NULL"
        status_origem = "status_maquina" if "status_maquina" in colunas else (
            "CASE WHEN ativo THEN 'Ativo' ELSE 'Inativo' END"
        )
        cursor.execute(
            f"""
            INSERT INTO maquinas_nova
                (id, patrimonio, empresa, tipo, modelo, usuario, setor, ativo,
                 observacao, status_maquina)
            SELECT
                id, patrimonio, empresa, tipo, modelo, usuario, setor, ativo,
                {observacao_origem}, {status_origem}
            FROM maquinas
            """
        )
        cursor.execute("DROP TABLE maquinas")
        cursor.execute("ALTER TABLE maquinas_nova RENAME TO maquinas")
        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()
        conexao.close()


def migrar_campos_visibilidade_maquina():
    """Adiciona status e oculta os patrimônios da lista até serem cadastrados."""
    conexao = db.engine.raw_connection()
    cursor = conexao.cursor()

    try:
        cursor.execute("PRAGMA table_info(maquinas)")
        colunas = {coluna[1] for coluna in cursor.fetchall()}
        if not colunas:
            return

        if "status_maquina" not in colunas:
            cursor.execute(
                "ALTER TABLE maquinas ADD COLUMN status_maquina "
                "VARCHAR(20) NOT NULL DEFAULT 'Ativo'"
            )
            cursor.execute(
                "UPDATE maquinas SET status_maquina = "
                "CASE WHEN ativo THEN 'Ativo' ELSE 'Inativo' END"
            )
        if "visivel" not in colunas:
            cursor.execute(
                "ALTER TABLE maquinas ADD COLUMN visivel "
                "BOOLEAN NOT NULL DEFAULT 1"
            )
            caminho_csv = Path(__file__).resolve().parent / "data" / "computadores.csv"
            if caminho_csv.exists():
                with caminho_csv.open(encoding="utf-8-sig", newline="") as arquivo:
                    for linha in csv.DictReader(arquivo):
                        partes = (linha.get("identificador") or "").strip().upper().split("-")
                        if len(partes) == 3 and partes[0]:
                            cursor.execute(
                                "UPDATE maquinas SET visivel = 0 WHERE patrimonio = ?",
                                (partes[0],)
                            )

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()


def adicionar_visibilidade_operacional():
    """Permite retirar itens das telas sem apagar o histórico relacionado."""
    conexao = db.engine.raw_connection()
    cursor = conexao.cursor()

    try:
        for tabela in ("atendimentos", "pecas"):
            cursor.execute(f"PRAGMA table_info({tabela})")
            colunas = {coluna[1] for coluna in cursor.fetchall()}
            if colunas and "visivel" not in colunas:
                cursor.execute(
                    f"ALTER TABLE {tabela} ADD COLUMN visivel "
                    "BOOLEAN NOT NULL DEFAULT 1"
                )
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()
