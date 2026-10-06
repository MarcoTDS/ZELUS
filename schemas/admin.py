from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import List, Optional
from schemas.unidade import UnidadeCreate

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
    unidades: List[UnidadeCreate] = Field(..., min_length=1, description="Unidades e áreas comuns a serem pré-cadastradas")

class CondominioUpdate(BaseModel):
    # RN15: Edição permitida a qualquer momento (apenas os campos informados são alterados)
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    cep: Optional[str] = Field(None, max_length=20)
    numero: Optional[str] = Field(None, max_length=6)
    rua: Optional[str] = Field(None, max_length=150)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$")

class SindicoResumo(BaseModel):
    id: int
    nome: str
    email: EmailStr
    email_validado: bool # RN12: False -> exibir "Reenviar link de validação"

    model_config = ConfigDict(from_attributes=True)

class CondominioResponse(BaseModel):
    id: int
    nome: str
    cep: str
    numero: str
    rua: str
    bairro: str
    cidade: str
    estado: str
    id_sindico: Optional[int] = None
    sindico: Optional[SindicoResumo] = None
    ativo: bool
    pode_inativar: Optional[bool] = None # RN15: Calculado na listagem do Administrador

    model_config = ConfigDict(from_attributes=True)

class CondominioPublicoResponse(BaseModel):
    # RF06: Dropdown de condomínios da Tela de Cadastro (dados públicos)
    id: int
    nome: str
    cidade: str
    estado: str

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SÍNDICO
# ==========================================
class SindicoCreate(BaseModel):
    id_condominio: int = Field(..., description="Condomínio do qual o síndico será responsável (RN07)")
    nome: str = Field(..., min_length=3, max_length=150)
    email: EmailStr

class SindicoCriadoResponse(BaseModel):
    id_usuario: int
    nome: str
    email: EmailStr
    id_condominio: Optional[int] = None
    # Retornados apenas para demonstração, enquanto não há envio real de e-mail (RN12, RN13)
    senha_provisoria: str
    link_validacao: str
