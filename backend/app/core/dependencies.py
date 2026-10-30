from fastapi import Header, HTTPException, Request
from .session import get_session

def obter_usuario(x_user_id: str | None = Header(default=None)):
    if not x_user_id or not get_session(x_user_id):
        raise HTTPException(401, "Sessão ausente ou expirada")
    return x_user_id

def obter_http_client(request: Request):
    return request.app.state.http_client
