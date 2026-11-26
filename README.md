# TI Manager

Sistema interno para gestão de atendimentos, máquinas e estoque de TI.

## Estrutura do projeto

```text
routes/      Rotas e regras de negócio
templates/   Páginas HTML
static/      CSS, JavaScript e imagens
instance/    Banco SQLite local (não versionado)
```

## Configuração

1. Crie e ative um ambiente virtual:

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Instale as dependências:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copie o arquivo de exemplo e defina uma chave secreta forte:

   ```powershell
   Copy-Item .env.example .env
   ```

   Configure no mínimo `SECRET_KEY`. O arquivo `.env` e o banco local não são enviados ao Git.

## Execução local

```powershell
.\venv\Scripts\python.exe app.py
```

O sistema será disponibilizado em `http://localhost:5000` e na rede local pela porta configurada em `PORT`.

O arquivo `data/computadores.csv` é opcional e pode conter identificadores e modelos usados para sugestões nos formulários. Para criar sua cópia local, use `data/computadores.example.csv` como referência; o arquivo local é ignorado pelo Git.

## Administradores

Contas novas começam como usuários comuns. Depois de criar uma conta, promova-a no ambiente virtual:

```powershell
.\venv\Scripts\flask.exe --app app.py promover-admin NOME_DO_USUARIO
```

Para remover a permissão administrativa:

```powershell
.\venv\Scripts\flask.exe --app app.py revogar-admin NOME_DO_USUARIO
```

## Execução para produção

Use o Waitress, em vez do servidor de desenvolvimento do Flask:

```powershell
.\venv\Scripts\waitress-serve.exe --host=0.0.0.0 --port=5000 app:app
```

Antes de publicar, defina uma `SECRET_KEY` exclusiva no ambiente de produção e configure o Firewall para a porta necessária. Para instalações com vários acessos simultâneos ou que precisem de backup centralizado, substitua o SQLite por um banco de dados gerenciado.
