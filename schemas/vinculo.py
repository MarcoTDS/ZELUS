from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from models.vinculo import StatusVinculoEnum
from schemas.unidade import UnidadeResumo
from schemas.usuario import UsuarioResumo, UsuarioResponse

class VinculoCreate(BaseModel):
    id_unidade: int = Field(..., description="ID da Unidade que o morador reside")

class VinculoAvaliar(BaseModel):
    aprovado: bool = Field(..., description="True para aprovar, False para rejeitar")

class VinculoResponse(BaseModel):
    id: int
    id_usuario: int
    id_unidade: int
    unidade: UnidadeResumo
    status_aprovacao: StatusVinculoEnum
    data_solicitacao: datetime
    data_avaliacao: Optional[datetime] = None
    ativo: bool

    model_config = ConfigDict(from_attributes=True)

class VinculoPendenteResponse(VinculoResponse):
    # RF11: Tela "Cadastros pendentes"
    usuario: UsuarioResumo
    responsavel_atual: Optional[str] = None # RN11: "Unidade já possui responsável: Fulano"

class MoradorResponse(BaseModel):
    # RF21: Tela "Gerenciamento de Moradores" (id = id do vínculo)
    id: int
    usuario: UsuarioResumo
    unidade: UnidadeResumo

    model_config = ConfigDict(from_attributes=True)

class CadastroMoradorResponse(BaseModel):
    # RF05, RF06: Resposta da Tela de Cadastro
    usuario: UsuarioResponse
    vinculo: VinculoResponse
    mensagem: str = "Cadastro enviado. Ele ficará pendente até a aprovação do síndico."
