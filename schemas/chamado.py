from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timedelta
from models.enums import StatusChamadoEnum
from typing import Optional

class ChamadoBase(BaseModel):
    titulo: str = Field(..., max_length=150)
    descricao: str
    id_unidade_destino: int
    id_categoria: int

class ChamadoCreate(ChamadoBase):
    id_usuario_autor: int
    foto_url: Optional[str] = None   # <-- Adicione esta linha
    video_url: Optional[str] = None  # <-- Adicione esta também, pelo mesmo motivo

class ChamadoResponse(ChamadoBase):
    id: int
    titulo: str
    descricao: str
    status: StatusChamadoEnum
    data_abertura: datetime
    prazo_sla_vigente: timedelta
    id_usuario_autor: int
    vencido: Optional[bool] = False 
    
    model_config = ConfigDict(from_attributes=True)

# Para o PATCH
class ChamadoStatusUpdate(BaseModel):
    novo_status: StatusChamadoEnum
    observacao: str = Field(..., min_length=5)

# Para a rota de GET detalhado
class ChamadoDetalheResponse(ChamadoResponse):
    foto_url: Optional[str] = None
    video_url: Optional[str] = None
    data_visto: Optional[datetime] = None

class ChamadoCriadoComAviso(BaseModel):
    chamado: ChamadoResponse
    aviso_similaridade: Optional[str] = None