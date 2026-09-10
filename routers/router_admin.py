from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.admin import CondominioCreate, SindicoCreate
from service import admin_service

def get_usuario_atual():
    # Placeholder de autenticação
    return {"id": 99, "perfil": "Admin"}

router_admin = APIRouter(prefix="/admin", tags=["Administrador"])

@router_admin.post("/condominios", status_code=status.HTTP_201_CREATED, summary="RF11 - Cadastro de Condomínio e Unidades")
def cadastrar_condominio_e_unidades(
    dados: CondominioCreate, 
    db: Session = Depends(get_db),
    usuario = Depends(get_usuario_atual)
):
    if usuario["perfil"] != "Admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao Administrador Geral.")
        
    condominio = admin_service.cadastrar_condominio_lote(db, dados)
    return {"mensagem": "Condomínio e unidades cadastrados com sucesso", "id_condominio": condominio.id}

@router_admin.post("/sindicos", status_code=status.HTTP_201_CREATED, summary="RF12 - Cadastro de Síndico")
def cadastrar_sindico(
    dados_sindico: SindicoCreate, 
    db: Session = Depends(get_db),
    usuario = Depends(get_usuario_atual)
):
    if usuario["perfil"] != "Admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao Administrador Geral.")
        
    resultado = admin_service.cadastrar_sindico(db, dados_sindico)
    return resultado