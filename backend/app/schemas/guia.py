from typing import Annotated

from pydantic import BaseModel, Field


class GuiaStreamRequest(BaseModel):
    destino: Annotated[str, Field(min_length=2, max_length=80)]
    dias_estadia: Annotated[int, Field(ge=1, le=5)] = 2
    estilo_viagem: Annotated[str, Field(min_length=3, max_length=40)] = "Cultural"
