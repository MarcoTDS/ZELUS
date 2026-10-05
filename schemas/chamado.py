from pydantic import BaseModel, ConfigDict, Field, computed_field
from datetime import datetime, timedelta
from models.enums import StatusChamadoEnum
from typing import List, Optional

class ChamadoBase(BaseModel):
    titulo: str = Field(..., max_length=150)
    descricao: str
    id_unidade_destino: int
    id_categoria: int

class ChamadoCreate(ChamadoBase):
    # O autor (id_usuario_autor) é o usuário logado, e o SLA é herdado da categoria (RN01)
    foto_url: Optional[str] = Field(None, max_length=255)
    video_url: Optional[str] = Field(None, max_length=255)

class ChamadoResponse(ChamadoBase):
    id: int
    status: StatusChamadoEnum
    data_abertura: datetime
    prazo_sla_vigente: timedelta
    id_usuario_autor: int
    vencido: Optional[bool] = False 

    @computed_field
    @property
    def data_vencimento(self) -> datetime:
        return self.data_abertura + self.prazo_sla_vigente
    
    model_config = ConfigDict(from_attributes=True)

# Para o PATCH
class ChamadoStatusUpdate(BaseModel):
    novo_status: StatusChamadoEnum
    observacao: str = Field(..., min_length=5)

class HistoricoChamadoResponse(BaseModel):
    id: int
    id_chamado: int
    data_alteracao: datetime
    status_anterior: StatusChamadoEnum
    novo_status: StatusChamadoEnum
    observacao: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Para a rota de GET detalhado
class ChamadoDetalheResponse(ChamadoResponse):
    foto_url: Optional[str] = None
    video_url: Optional[str] = None
    data_visto: Optional[datetime] = None
    historico: List[HistoricoChamadoResponse] = [] # RN03: Preenchido pelo relationship ChamadoDB.historico

class ChamadoCriadoComAviso(BaseModel):
    chamado: ChamadoResponse
    aviso_similaridade: Optional[str] = None