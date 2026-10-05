from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import List, Optional
from models.enums import TipoCondominioEnum

# ==========================================
# UNIDADES
# ==========================================
class UnidadeCreate(BaseModel):
    # Apartamento: informe "apartamento" (obrigatório) e "bloco" (opcional)
    # Casa: informe "numero_casa" (obrigatório) e "rua" (opcional)
    bloco: Optional[str] = Field(None, max_length=50, description="Bloco/torre (condomínio de apartamentos)")
    apartamento: Optional[str] = Field(None, max_length=50, description="Número do apartamento")
    rua: Optional[str] = Field(None, max_length=150, description="Rua interna (condomínio de casas)")
    numero_casa: Optional[str] = Field(None, max_length=50, description="Número da casa")

class UnidadeResponse(BaseModel):
    id: int
    id_condominio: int
    tipo_condominio: TipoCondominioEnum
    bloco: Optional[str] = None
    apartamento: Optional[str] = None
    rua: Optional[str] = None
    numero_casa: Optional[str] = None
    ativo: bool

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# CONDOMÍNIO
# ==========================================
class CondominioCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=100)
    cep: str = Field(..., max_length=20)
    numero: str = Field(..., max_length=6, description="Número do endereço do condomínio")
    rua: str = Field(..., max_length=150)
    bairro: str = Field(..., max_length=100)
    cidade: str = Field(..., max_length=100)
    estado: str = Field(..., min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$", description="Sigla da UF (ex: PR)")
    id_sindico: int = Field(..., description="ID do usuário síndico responsável (RN07)")
    tipo_condominio: TipoCondominioEnum = Field(..., description="Casa ou Apartamento (aplicado a todas as unidades)")
    unidades: List[UnidadeCreate] = Field(..., min_length=1, description="Lista de unidades a serem pré-cadastradas")

class CondominioResponse(BaseModel):
    id: int
    nome: str
    cep: str
    numero: str
    rua: str
    bairro: str
    cidade: str
    estado: str
    id_sindico: int
    ativo: bool

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SÍNDICO
# ==========================================
class SindicoCreate(BaseModel):
    nome: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    id_condominio: Optional[int] = Field(None, description="Se informado, o síndico passa a ser o responsável por este condomínio (RN07)")

class SindicoCriadoResponse(BaseModel):
    id_usuario: int
    nome: str
    email: EmailStr
    id_condominio: Optional[int] = None
    senha_provisoria: str # Retornada apenas para demonstração, enquanto não há envio de e-mail (RN13)