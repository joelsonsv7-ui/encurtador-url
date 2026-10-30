"""URL Shortener API - FastAPI application."""

import secrets

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse

import storage
from models import URLCreate, URLResponse

app = FastAPI(title="Encurtador de URLs", version="1.0.0")


@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    """Endpoint de saúde da aplicação."""
    return {"status": "ok"}


@app.post(
    "/encurtar",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar URL curta",
    description="Recebe uma URL longa e retorna um código curto de 6 caracteres."
)
def encurtar(payload: URLCreate) -> URLResponse:
    """Cria uma URL curta a partir de uma URL longa."""
    for _ in range(3):
        code = secrets.token_urlsafe(6)[:6]
        if not storage.get_url(code):
            storage.save_url(code, str(payload.url))
            return URLResponse(
                codigo=code,
                url_curta=f"http://localhost:8000/{code}"
            )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Falha ao gerar código único após 3 tentativas"
    )


@app.get(
    "/{code}",
    summary="Redirecionar para URL original",
    description="Redireciona o usuário para a URL original correspondente ao código."
)
def redirecionar(code: str) -> RedirectResponse:
    """Redireciona para a URL original."""
    url = storage.get_url(code)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código não encontrado"
        )
    return RedirectResponse(url=url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)