from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.admin import CondominioCreate, CondominioResponse, SindicoCreate, SindicoCriadoResponse
from schemas.usuario import UsuarioResponse
from service import admin_service, usuario_service

def get_usuario_atual():
    # Placeholder de autenticação
    return {"id": 99, "perfil": "Administrador"}

def validar_administrador(usuario: dict):
    if usuario["perfil"] != "Administrador":
        raise HTTPException(status_code=403, detail="Acesso restrito ao Administrador Geral.")

router_admin = APIRouter(prefix="/admin", tags=["Administrador"])

@router_admin.post("/condominios", response_model=CondominioResponse, status_code=status.HTTP_201_CREATED, summary="RF11 - Cadastro de Condomínio e Unidades")
def cadastrar_condominio_e_unidades(
    dados: CondominioCreate, 
    db: Session = Depends(get_db),
    usuario = Depends(get_usuario_atual)
):
    validar_administrador(usuario)
    return admin_service.cadastrar_condominio_lote(db, dados)

@router_admin.post("/sindicos", response_model=SindicoCriadoResponse, status_code=status.HTTP_201_CREATED, summary="RF12 - Cadastro de Síndico")
def cadastrar_sindico(
    dados_sindico: SindicoCreate, 
    db: Session = Depends(get_db),
    usuario = Depends(get_usuario_atual)
):
    validar_administrador(usuario)
    return admin_service.cadastrar_sindico(db, dados_sindico)

@router_admin.patch("/usuarios/{id_usuario}/inativar", response_model=UsuarioResponse, summary="Inativação de Usuário (Soft Delete)")
def inativar_usuario(
    id_usuario: int,
    db: Session = Depends(get_db),
    usuario = Depends(get_usuario_atual)
):
    validar_administrador(usuario)
    try:
        return usuario_service.inativar_usuario(db, id_usuario)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))