from pydantic import BaseModel, Field


class GoogleTokenRequest(BaseModel):
    credential: str = Field(min_length=20)


class UserProfile(BaseModel):
    id: str
    nome: str
    email: str
    foto: str = ""
    visitante: bool = False


class LoginResponse(BaseModel):
    usuario: UserProfile
    expires_in: int | None = None
