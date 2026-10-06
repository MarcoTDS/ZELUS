from pydantic import BaseModel, ConfigDict, Field, computed_field
from datetime import datetime, timedelta
from models.enums import StatusChamadoEnum
from schemas.categoria import CategoriaResumo
from schemas.unidade import UnidadeResumo
from typing import List, Literal, Optional

class ChamadoCreate(BaseModel):
    # RF07: O autor é o morador logado e o SLA é herdado da categoria (RN01)
    titulo: str = Field(..., min_length=3, max_length=150)
    descricao: str = Field(..., min_length=3)
    id_categoria: int
    id_unidade_destino: int = Field(..., description="Unidade do morador ou área comum (RN05)")
    foto_url: Optional[str] = Field(None, max_length=255)
    video_url: Optional[str] = Field(None, max_length=255)

class AutorResumo(BaseModel):
    id: int
    nome: str

    model_config = ConfigDict(from_attributes=True)

class ChamadoResponse(BaseModel):
    # Itens das listas: Meus Chamados, Mural, Worklist e Histórico de Chamados
    id: int
    titulo: str
    descricao: str
    status: StatusChamadoEnum
    data_abertura: datetime
    prazo_sla_vigente: timedelta
    id_usuario_autor: int
    id_unidade_destino: int
    id_categoria: int
    categoria: CategoriaResumo
    unidade: UnidadeResumo
    vencido: bool = False
    urgencia: Optional[Literal["Vencido", "Alta", "Media", "Baixa"]] = None # RN04: Cor exibida (None se finalizado)

    @computed_field
    @property
    def data_vencimento(self) -> datetime:
        return self.data_abertura + self.prazo_sla_vigente
    
    model_config = ConfigDict(from_attributes=True)

class HistoricoChamadoResponse(BaseModel):
    id: int
    id_chamado: int
    data_alteracao: datetime
    status_anterior: StatusChamadoEnum
    novo_status: StatusChamadoEnum
    observacao: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ChamadoDetalheResponse(ChamadoResponse):
    # RF18: Tela de detalhe/gerenciamento do chamado
    autor: AutorResumo
    foto_url: Optional[str] = None
    video_url: Optional[str] = None
    data_visto: Optional[datetime] = None            # RN10
    data_conclusao: Optional[datetime] = None
    concluido_no_prazo: Optional[bool] = None        # "Concluído dentro do prazo"
    historico: List[HistoricoChamadoResponse] = []   # RN03

class ChamadoStatusUpdate(BaseModel):
    novo_status: StatusChamadoEnum
    observacao: str = Field(..., min_length=3)

class ChamadoCriadoComAviso(BaseModel):
    chamado: ChamadoResponse
    aviso_similaridade: Optional[str] = None # RN09

class SimilaridadeResponse(BaseModel):
    # RN09: Consulta feita pelo front enquanto o morador preenche o formulário
    existe_similar: bool
    id_chamado: Optional[int] = None

class ResumoSindicoResponse(BaseModel):
    # RF03: "Resumo" do Dashboard do Síndico
    abertos: int
    urgentes: int
    vencidos: int
