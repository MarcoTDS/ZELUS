from pydantic import BaseModel, Field

class VinculoCreate(BaseModel):
    id_unidade: int = Field(..., description="ID da Unidade que o morador reside")

class VinculoAvaliar(BaseModel):
    aprovado: bool = Field(..., description="True para aprovar, False para rejeitar")