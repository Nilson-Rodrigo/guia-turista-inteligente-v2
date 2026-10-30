from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


Cidade = Annotated[str, Field(min_length=2, max_length=80)]
UF = Annotated[str, Field(min_length=2, max_length=2)]


class RoteiroRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    origem_cidade: Cidade
    origem_uf: UF
    destino_cidade: Cidade
    destino_uf: UF
    dias_estadia: int = Field(default=2, ge=1, le=5)
    estilo_viagem: str = Field(default="Cultural", max_length=80)

    @field_validator("origem_uf", "destino_uf")
    @classmethod
    def validar_uf(cls, valor: str) -> str:
        valor = valor.upper()
        if valor not in "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split():
            raise ValueError("A UF deve conter exatamente duas letras")
        return valor


class RoteiroResponse(BaseModel):
    id: str
    origem: str
    destino: str
    origem_coordenadas: list[float] = [0.0, 0.0]
    destino_coordenadas: list[float] = [0.0, 0.0]
    clima: dict[str, str]
    percurso: dict[str, str]
    guia_status: str

    dias_estadia: int = 2
    estilo_viagem: str = "Cultural"
    atrativos: list[dict] = Field(default_factory=list)
    gastronomia: list[str] = Field(default_factory=list)
    visitas: list[str] = Field(default_factory=list)
