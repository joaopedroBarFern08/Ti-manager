from urllib.parse import urlsplit

from flask import request


def obter_proxima_url():
    """Retorna somente destinos internos informados na navegação."""
    proximo = request.values.get("proximo", "").strip()
    destino = urlsplit(proximo)

    if (
        proximo.startswith("/")
        and not proximo.startswith("//")
        and not destino.scheme
        and not destino.netloc
    ):
        return proximo

    return None
