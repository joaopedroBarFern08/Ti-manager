# TI Manager

Sistema de gerenciamento de TI desenvolvido em Flask.

## Tecnologias

- Python
- Flask
- SQLAlchemy
- SQLite

## Instalação

Para executar o projeto em outra máquina, primeiro clone o repositório e entre na pasta do projeto. Depois, crie um novo ambiente virtual com "python -m venv venv" e ative-o com .\venv\Scripts\Activate.ps1. Com o ambiente ativado, instale as dependências utilizando "pip install -r requirements.txt".

Em seguida, copie o arquivo .env.example para .env utilizando "Copy-Item .env.example .env" e configure a a SECRET_KEY. 

Por fim, execute o sistema com python app.py e acesse http://127.0.0.1:5000 pelo navegador.

O projeto utiliza SQLite e o banco de dados ti_manager.db é criado automaticamente na primeira execução. Como o banco não é versionado no GitHub, cada máquina terá seu próprio banco de dados.

As pastas e arquivos venv/, .env, *.db e __pycache__/ não devem ser enviados para o repositório.
