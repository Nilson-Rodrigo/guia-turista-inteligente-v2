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

    @field_validator("origem_uf", "destino_uf")
    @classmethod
    def validar_uf(cls, valor: str) -> str:
        valor = valor.upper()
        if not valor.isalpha() or len(valor) != 2:
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
