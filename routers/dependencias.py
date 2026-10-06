from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from service import auth_service

# No Swagger (/docs), use o botão "Authorize" e cole o access_token retornado pelo /auth/login
esquema_bearer = HTTPBearer(auto_error=False)

def get_usuario_autenticado(
    credenciais: HTTPAuthorizationCredentials = Depends(esquema_bearer),
    db: Session = Depends(get_db)
) -> dict:
    """Usuário logado, sem exigir a troca da senha provisória (usado no /auth/me e na troca de senha)."""
    if not credenciais:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado.", headers={"WWW-Authenticate": "Bearer"})
    try:
        return auth_service.montar_usuario_atual(db, credenciais.credentials)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e), headers={"WWW-Authenticate": "Bearer"})

def get_usuario_atual(usuario: dict = Depends(get_usuario_autenticado)) -> dict:
    """RN13: Bloqueia o restante do sistema enquanto a senha provisória não for trocada."""
    if usuario["senha_provisoria"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Troque a senha provisória antes de continuar.")
    return usuario

def exigir_perfil(*perfis: str):
    def dependencia(usuario: dict = Depends(get_usuario_atual)) -> dict:
        if usuario["perfil"] not in perfis:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não permitido para o seu perfil.")

        # RN14: Síndico sem condomínio vinculado não tem acesso aos dados
        if usuario["perfil"] == "Sindico" and usuario["id_condominio"] is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Síndico sem condomínio vinculado.")

        # Morador com cadastro pendente: o login é permitido, mas as funcionalidades só após a aprovação
        if usuario["perfil"] == "Morador" and usuario["status_vinculo"] != "Aprovado":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seu cadastro ainda está pendente de aprovação pelo síndico.")

        return usuario
    return dependencia

get_administrador = exigir_perfil("Administrador")
get_sindico = exigir_perfil("Sindico")
get_morador = exigir_perfil("Morador")
get_morador_ou_sindico = exigir_perfil("Morador", "Sindico")
