from pydantic import BaseModel, ConfigDict, Field, computed_field
from datetime import timedelta
from typing import Literal, Optional

class CategoriaCreate(BaseModel):
    # O condomínio é o do síndico logado (RN14)
    nome: str = Field(..., min_length=3, max_length=100, description="Ex: Hidráulica")
    prazo_sla: int = Field(..., gt=0, description="Prazo de SLA (ex: 24)")
    unidade_prazo: Literal["horas", "dias"] = Field("horas", description="RF08: Prazo informado em horas ou dias")

class CategoriaUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    prazo_sla: Optional[int] = Field(None, gt=0)
    unidade_prazo: Literal["horas", "dias"] = "horas"
    ativo: Optional[bool] = None

class CategoriaResumo(BaseModel):
    id: int
    nome: str

    model_config = ConfigDict(from_attributes=True)

class CategoriaResponse(CategoriaResumo):
    id_condominio: int
    prazo_sla: timedelta
    ativo: bool

    @computed_field
    @property
    def prazo_sla_horas(self) -> float:
        return self.prazo_sla.total_seconds() / 3600
