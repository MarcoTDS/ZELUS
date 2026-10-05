from pydantic import BaseModel, ConfigDict, Field
from models.vinculo import StatusVinculoEnum

class VinculoCreate(BaseModel):
    id_unidade: int = Field(..., description="ID da Unidade que o morador reside")

class VinculoAvaliar(BaseModel):
    aprovado: bool = Field(..., description="True para aprovar, False para rejeitar")

class VinculoResponse(BaseModel):
    id: int
    id_usuario: int
    id_unidade: int
    status_aprovacao: StatusVinculoEnum
    ativo: bool

    model_config = ConfigDict(from_attributes=True)