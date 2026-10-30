import httpx
from fastapi import APIRouter, Header, HTTPException, Request, status

from ..core.config import get_settings
from ..core.session import create_visitor, delete_session, get_session
from ..schemas.auth import GoogleTokenRequest, LoginResponse, UserProfile

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])


@router.post("/demo", response_model=LoginResponse)
async def login_demo() -> LoginResponse:
    record = create_visitor()
    return LoginResponse(usuario=UserProfile(**record.profile), expires_in=7200)


@router.post("/google", response_model=LoginResponse)
async def login_google(payload: GoogleTokenRequest, request: Request) -> LoginResponse:
    settings = get_settings()
    client: httpx.AsyncClient = request.app.state.http_client
    try:
        response = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": payload.credential},
        )
        response.raise_for_status()
        token = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(status_code=401, detail="Token Google inválido") from error
    if settings.google_client_id and token.get("aud") != settings.google_client_id:
        raise HTTPException(status_code=401, detail="Token não pertence a este cliente")
    user_id = str(token.get("sub", ""))
    if not user_id or not token.get("email"):
        raise HTTPException(status_code=401, detail="Perfil Google incompleto")
    from ..core.session import SessionRecord, sessions
    record = SessionRecord(
        user_id=user_id,
        profile={
            "id": user_id,
            "nome": token.get("name", token["email"]),
            "email": token["email"],
            "foto": token.get("picture", ""),
            "visitante": False,
        },
    )
    sessions[user_id] = record
    return LoginResponse(usuario=UserProfile(**record.profile))


@router.get("/me", response_model=UserProfile)
async def current_user(x_user_id: str | None = Header(default=None)) -> UserProfile:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id ausente")
    record = get_session(x_user_id)
    if not record:
        raise HTTPException(status_code=401, detail="Sessão ausente ou expirada")
    return UserProfile(**record.profile)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(x_user_id: str | None = Header(default=None)) -> None:
    if x_user_id:
        delete_session(x_user_id)
