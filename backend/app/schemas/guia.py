from pydantic import BaseModel, Field
class GuiaStreamRequest(BaseModel):
    destino: str = Field(min_length=2, max_length=100)
    dias_estadia: int = Field(default=2, ge=1, le=5)
    estilo_viagem: str = Field(default="Cultural", max_length=80)
    clima_info: dict = Field(default_factory=dict)
    atrativos: list = Field(default_factory=list)
    gastronomia: list = Field(default_factory=list)
