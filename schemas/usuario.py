from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from typing import Optional
from models.enums import PerfilUsuarioEnum

# ==========================================
# SCHEMAS DE CRIAÇÃO E LEITURA DE USUÁRIO
# ==========================================
class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    perfil: PerfilUsuarioEnum = PerfilUsuarioEnum.Morador

class UsuarioCreate(UsuarioBase):
    # O bcrypt aceita no máximo 72 bytes de senha
    senha: str = Field(..., min_length=6, max_length=72, description="Senha em texto plano (será hasheada)")

class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    perfil: PerfilUsuarioEnum
    ultimo_acesso: Optional[datetime] = None
    ativo: bool

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SCHEMAS DE AUTENTICAÇÃO E PERFIL
# ==========================================
class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(..., description="Senha em texto plano")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    requer_troca_senha: bool # RN13: True no primeiro acesso (ultimo_acesso ainda vazio)

class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str = Field(..., min_length=6, max_length=72)

class EditarPerfilRequest(BaseModel):
    novo_email: EmailStr