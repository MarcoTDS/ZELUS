from pydantic import BaseModel, ConfigDict, Field, computed_field
from datetime import timedelta
from typing import Optional

class CategoriaCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100, description="Ex: Hidráulica")
    prazo_sla_horas: int = Field(..., gt=0, description="Prazo de SLA em horas (ex: 48)")
    id_condominio: int

class CategoriaUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    prazo_sla_horas: Optional[int] = Field(None, gt=0)
    ativo: Optional[bool] = None

class CategoriaResponse(BaseModel):
    id: int
    id_condominio: int
    nome: str
    prazo_sla: timedelta
    ativo: bool

    @computed_field
    @property
    def prazo_sla_horas(self) -> float:
        return self.prazo_sla.total_seconds() / 3600

    model_config = ConfigDict(from_attributes=True)