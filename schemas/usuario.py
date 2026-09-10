from pydantic import BaseModel, EmailStr, Field
from models.enums import PerfilUsuarioEnum

# ==========================================
# SCHEMAS DE CRIAÇÃO E LEITURA DE USUÁRIO
# ==========================================
class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    perfil: PerfilUsuarioEnum

class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=6, description="Senha em texto plano (será hasheada)")

class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    perfil: str

    class Config:
        from_attributes = True

# ==========================================
# SCHEMAS DE AUTENTICAÇÃO E PERFIL
# ==========================================
class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(..., description="Senha em texto plano")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    requer_troca_senha: bool

class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str = Field(..., min_length=6)

class EditarPerfilRequest(BaseModel):
    novo_email: EmailStr