from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from models.enums import TipoUnidadeEnum

# Apartamento: informe "apartamento" (obrigatório) e "bloco" (opcional)
# Casa: informe "numero_casa" (obrigatório) e "rua" (opcional)
# Area Comum: informe "descricao" (obrigatório, ex: Garagem)

class UnidadeCreate(BaseModel):
    tipo_unidade: TipoUnidadeEnum
    bloco: Optional[str] = Field(None, max_length=50, description="Bloco/torre (apartamentos)")
    apartamento: Optional[str] = Field(None, max_length=50, description="Número do apartamento")
    rua: Optional[str] = Field(None, max_length=150, description="Rua interna (casas)")
    numero_casa: Optional[str] = Field(None, max_length=50, description="Número da casa")
    descricao: Optional[str] = Field(None, max_length=100, description="Nome da área comum (ex: Garagem)")

class UnidadeUpdate(BaseModel):
    # Apenas os campos enviados são alterados (um campo enviado como null é limpo)
    tipo_unidade: Optional[TipoUnidadeEnum] = None
    bloco: Optional[str] = Field(None, max_length=50)
    apartamento: Optional[str] = Field(None, max_length=50)
    rua: Optional[str] = Field(None, max_length=150)
    numero_casa: Optional[str] = Field(None, max_length=50)
    descricao: Optional[str] = Field(None, max_length=100)

class UnidadeResumo(BaseModel):
    # Usado em listas e dropdowns: "Bloco A, Apto 21", "Rua 1, Casa 5", "Garagem"
    id: int
    tipo_unidade: TipoUnidadeEnum
    identificacao: str

    model_config = ConfigDict(from_attributes=True)

class UnidadeResponse(UnidadeResumo):
    id_condominio: int
    bloco: Optional[str] = None
    apartamento: Optional[str] = None
    rua: Optional[str] = None
    numero_casa: Optional[str] = None
    descricao: Optional[str] = None
    ativo: bool
    responsavel: Optional[str] = None # RN17: Morador responsável (impede a inativação)
