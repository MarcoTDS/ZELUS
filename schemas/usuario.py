from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from datetime import datetime
from typing import Optional
from models.enums import PerfilUsuarioEnum

# O bcrypt aceita no máximo 72 bytes de senha
SENHA_MIN = 6
SENHA_MAX = 72

class ConfirmacaoSenhaMixin(BaseModel):
    # Telas 1.8, 1.17 e 1.18: "Nova senha" e "Confirmar nova senha"
    @model_validator(mode="after")
    def validar_confirmacao(self):
        if self.nova_senha != self.confirmar_nova_senha:
            raise ValueError("A confirmação não confere com a nova senha.")
        return self

# ==========================================
# SCHEMAS DE CRIAÇÃO E LEITURA DE USUÁRIO
# ==========================================
class UsuarioBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    perfil: PerfilUsuarioEnum = PerfilUsuarioEnum.Morador

class UsuarioCreate(UsuarioBase):
    senha: str = Field(..., min_length=SENHA_MIN, max_length=SENHA_MAX, description="Senha em texto plano (será hasheada)")

class CadastroMoradorRequest(BaseModel):
    # RF05, RF06: Tela de Cadastro (dados do morador + unidade solicitada)
    nome: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    senha: str = Field(..., min_length=SENHA_MIN, max_length=SENHA_MAX)
    id_unidade: int = Field(..., description="Unidade escolhida no cadastro (fica pendente até a aprovação do síndico)")

class UsuarioResumo(BaseModel):
    id: int
    nome: str
    email: EmailStr
    ativo: bool

    model_config = ConfigDict(from_attributes=True)

class UsuarioResponse(UsuarioResumo):
    perfil: PerfilUsuarioEnum
    ultimo_acesso: Optional[datetime] = None
    email_validado: bool
    senha_provisoria: bool

# ==========================================
# SCHEMAS DE AUTENTICAÇÃO E PERFIL
# ==========================================
class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(..., description="Senha em texto plano")

class UsuarioLogadoResponse(BaseModel):
    # Dados do usuário logado, usados pelo front para escolher a tela inicial
    id: int
    nome: str
    email: EmailStr
    perfil: PerfilUsuarioEnum
    id_condominio: Optional[int] = None
    senha_provisoria: bool               # RN13: True -> tela "Defina sua senha"
    status_vinculo: Optional[str] = None # Morador: "Pendente" -> tela de pendência

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioLogadoResponse

class AlterarSenhaRequest(ConfirmacaoSenhaMixin):
    senha_atual: str
    nova_senha: str = Field(..., min_length=SENHA_MIN, max_length=SENHA_MAX)
    confirmar_nova_senha: str

class EditarPerfilRequest(BaseModel):
    # RF15, RF21: Apenas os campos informados são alterados
    nome: Optional[str] = Field(None, min_length=3, max_length=150)
    email: Optional[EmailStr] = None

class EsqueciSenhaRequest(BaseModel):
    email: EmailStr

class RedefinirSenhaRequest(ConfirmacaoSenhaMixin):
    token: str = Field(..., description="Token recebido no link do e-mail")
    nova_senha: str = Field(..., min_length=SENHA_MIN, max_length=SENHA_MAX)
    confirmar_nova_senha: str

class ValidarEmailRequest(BaseModel):
    token: str = Field(..., description="Token recebido no link do e-mail")

class MensagemResponse(BaseModel):
    mensagem: str
