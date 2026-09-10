from pydantic import BaseModel, Field
from typing import Optional

class CategoriaCreate(BaseModel):
    nome: str = Field(..., min_length=3, description="Ex: Hidráulica")
    prazo_sla_horas: int = Field(..., gt=0, description="Prazo de SLA em horas (ex: 48)")
    id_condominio: int

class CategoriaUpdate(BaseModel):
    nome: Optional[str] = None
    prazo_sla_horas: Optional[int] = None
    ativo: Optional[bool] = None