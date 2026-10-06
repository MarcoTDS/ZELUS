from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas.usuario import (LoginRequest, LoginResponse, UsuarioLogadoResponse, UsuarioResponse, CadastroMoradorRequest,
                             AlterarSenhaRequest, EditarPerfilRequest, EsqueciSenhaRequest, RedefinirSenhaRequest,
                             ValidarEmailRequest, MensagemResponse)
from schemas.unidade import UnidadeResumo
from schemas.vinculo import CadastroMoradorResponse
from service import usuario_service, auth_service, vinculo_service
from routers.dependencias import get_usuario_autenticado, get_usuario_atual

router_auth = APIRouter(prefix="/auth", tags=["Autenticação & Perfil"])

# ==========================================
# ROTAS PÚBLICAS
# ==========================================
@router_auth.post("/login", response_model=LoginResponse, summary="RF01 - Login")
def login(credenciais: LoginRequest, db: Session = Depends(get_db)):
    """RF01, RN12, RN13 - Autentica o usuário e retorna o token JWT e os dados para escolher a tela inicial."""
    try:
        usuario = usuario_service.autenticar_usuario(db, credenciais.email, credenciais.senha)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) # RN12: e-mail não validado
    
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos.")
    
    token = auth_service.criar_access_token(usuario)
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": auth_service.montar_usuario_atual(db, token)
    }

@router_auth.post("/cadastro", response_model=CadastroMoradorResponse, status_code=status.HTTP_201_CREATED, summary="RF05/RF06 - Cadastro do Morador")
def cadastrar_morador(dados: CadastroMoradorRequest, db: Session = Depends(get_db)):
    """RF05, RF06, RN11 - Cria o morador e a solicitação de vínculo, pendente até a aprovação do síndico."""
    try:
        usuario, vinculo = usuario_service.cadastrar_morador(db, dados)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return {"usuario": usuario, "vinculo": vinculo}

@router_auth.post("/validar-email", response_model=MensagemResponse, summary="RN12 - Validação do e-mail do síndico")
def validar_email(dados: ValidarEmailRequest, db: Session = Depends(get_db)):
    try:
        usuario_service.validar_email(db, dados.token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"mensagem": "E-mail validado com sucesso. Faça login com a senha provisória recebida."}

@router_auth.post("/esqueci-senha", response_model=MensagemResponse, summary="RF19 - Solicitar redefinição de senha")
def esqueci_senha(dados: EsqueciSenhaRequest, db: Session = Depends(get_db)):
    """RF19, RN16 - A resposta é sempre a mesma, exista ou não o e-mail (evita descobrir contas cadastradas)."""
    usuario_service.solicitar_redefinicao_senha(db, dados.email)
    return {"mensagem": "E-mail enviado! Verifique sua caixa de entrada."}

@router_auth.post("/redefinir-senha", response_model=MensagemResponse, summary="RN16 - Definir nova senha pelo link")
def redefinir_senha(dados: RedefinirSenhaRequest, db: Session = Depends(get_db)):
    try:
        usuario_service.redefinir_senha(db, dados.token, dados.nova_senha)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"mensagem": "Senha redefinida com sucesso. Faça login com a nova senha."}

# ==========================================
# ROTAS DO USUÁRIO LOGADO
# ==========================================
@router_auth.get("/me", response_model=UsuarioLogadoResponse, summary="Dados do usuário logado")
def obter_usuario_logado(usuario_atual: dict = Depends(get_usuario_autenticado)):
    """Usado pelo front para decidir a tela: troca de senha (RN13), pendência (morador) ou dashboard."""
    return usuario_atual

@router_auth.patch("/me/senha", response_model=UsuarioResponse, summary="RF15/RF16 - Alterar a própria senha")
def alterar_senha_propria(
    dados_senha: AlterarSenhaRequest, 
    db: Session = Depends(get_db), 
    usuario_atual: dict = Depends(get_usuario_autenticado) # Permitida também com senha provisória (RN13)
):
    """RF15, RF16, RN13 - Troca de senha, inclusive a da senha provisória no primeiro acesso."""
    try:
        return usuario_service.alterar_senha(db, usuario_atual["id"], dados_senha.senha_atual, dados_senha.nova_senha)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router_auth.patch("/me", response_model=UsuarioResponse, summary="RF15 - Editar o próprio perfil")
def editar_perfil(
    dados_perfil: EditarPerfilRequest, 
    db: Session = Depends(get_db), 
    usuario_atual: dict = Depends(get_usuario_atual)
):
    try:
        return usuario_service.atualizar_perfil(db, usuario_atual["id"], dados_perfil.nome, dados_perfil.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router_auth.get("/me/unidades", response_model=List[UnidadeResumo], summary="Unidades aprovadas do morador logado")
def listar_minhas_unidades(db: Session = Depends(get_db), usuario_atual: dict = Depends(get_usuario_atual)):
    """Tela Editar Perfil (campo Unidade, somente leitura)."""
    return vinculo_service.listar_unidades_do_morador(db, usuario_atual["id"])
