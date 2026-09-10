from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.usuario import LoginRequest, LoginResponse, AlterarSenhaRequest, EditarPerfilRequest, UsuarioCreate, UsuarioResponse
from service import usuario_service

# Dependência fictícia para extrair o usuário logado do Token JWT
def get_usuario_atual():
    # Em produção, isso decodificaria o token JWT do header Authorization
    return {"id": 1, "perfil": "Sindico", "email": "sindico@condominio.com"}

router_auth = APIRouter(prefix="/auth", tags=["Autenticação & Perfil"])

@router_auth.post("/signup", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(dados_usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # Verifica se já existe um usuário cadastrado com o mesmo e-mail
    usuario_existente = usuario_service.obter_usuario_por_email(db, email=dados_usuario.email)
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um usuário cadastrado com este e-mail."
        )
    
    # Cria o novo usuário no banco
    novo_usuario = usuario_service.criar_usuario(db, dados_usuario)
    return novo_usuario

@router_auth.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(credenciais: LoginRequest, db: Session = Depends(get_db)):
    """RF01, RN13 - Autentica o usuário e sinaliza se é necessário trocar a senha provisória."""
    usuario = usuario_service.autenticar_usuario(db, credenciais.email, credenciais.senha)
    
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="E-mail ou senha incorretos."
        )
    
    # Aqui geraríamos o token JWT real. Usando um token simulado para o exemplo.
    token_jwt = f"token_jwt_simulado_para_{usuario.id}"
    
    return {
        "access_token": token_jwt,
        "token_type": "bearer",
        "requer_troca_senha": usuario.senha_provisoria # RN13
    }

@router_auth.patch("/me/senha", response_model=UsuarioResponse)
def alterar_senha_propria(
    dados_senha: AlterarSenhaRequest, 
    db: Session = Depends(get_db), 
    usuario_atual = Depends(get_usuario_atual)
):
    """RF14, RF15, RN13 - Permite a troca de senha e remove a flag de senha provisória."""
    try:
        usuario_atualizado = usuario_service.alterar_senha(
            db=db, 
            id_usuario=usuario_atual["id"], 
            senha_atual=dados_senha.senha_atual, 
            nova_senha=dados_senha.nova_senha
        )
        return usuario_atualizado
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router_auth.patch("/me", response_model=UsuarioResponse)
def editar_perfil(
    dados_perfil: EditarPerfilRequest, 
    db: Session = Depends(get_db), 
    usuario_atual = Depends(get_usuario_atual)
):
    """RF14 - Permite que o usuário (ex: Morador) atualize seu e-mail de contato."""
    # Valida se o novo e-mail já está em uso por outra pessoa
    email_existente = usuario_service.buscar_por_email(db, dados_perfil.novo_email)
    if email_existente and email_existente.id != usuario_atual["id"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já está em uso.")
    
    usuario_atualizado = usuario_service.atualizar_perfil(
        db=db, 
        id_usuario=usuario_atual["id"], 
        novo_email=dados_perfil.novo_email
    )
    return usuario_atualizado