from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas.admin import CondominioCreate, CondominioUpdate, CondominioResponse, SindicoCreate, SindicoCriadoResponse
from schemas.unidade import UnidadeCreate, UnidadeUpdate, UnidadeResponse
from schemas.usuario import UsuarioResponse
from service import admin_service, unidade_service, usuario_service
from routers.dependencias import get_administrador

# Todas as rotas exigem o perfil Administrador
router_admin = APIRouter(prefix="/admin", tags=["Administrador"], dependencies=[Depends(get_administrador)])

def _condominio_ou_404(db: Session, id_condominio: int):
    condominio = admin_service.buscar_condominio(db, id_condominio)
    if not condominio:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")
    return condominio

# ==========================================
# CONDOMÍNIOS (RF04, RF12, RN15)
# ==========================================
@router_admin.get("/condominios", response_model=List[CondominioResponse], summary="RF04 - Condomínios cadastrados")
def listar_condominios(incluir_inativos: bool = Query(False), db: Session = Depends(get_db)):
    return admin_service.listar_condominios(db, incluir_inativos)

@router_admin.post("/condominios", response_model=CondominioResponse, status_code=status.HTTP_201_CREATED, summary="RF12 - Cadastro de Condomínio e Unidades")
def cadastrar_condominio_e_unidades(dados: CondominioCreate, db: Session = Depends(get_db)):
    return admin_service.cadastrar_condominio_lote(db, dados)

@router_admin.put("/condominios/{id_condominio}", response_model=CondominioResponse, summary="RN15 - Editar Condomínio")
def editar_condominio(id_condominio: int, dados: CondominioUpdate, db: Session = Depends(get_db)):
    condominio = admin_service.editar_condominio(db, id_condominio, dados)
    if not condominio:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")
    return condominio

@router_admin.patch("/condominios/{id_condominio}/inativar", response_model=CondominioResponse, summary="RN15 - Inativar Condomínio")
def inativar_condominio(id_condominio: int, db: Session = Depends(get_db)):
    condominio = admin_service.inativar_condominio(db, id_condominio)
    if not condominio:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")
    return condominio

# ==========================================
# UNIDADES DE UM CONDOMÍNIO (RF20, RN17)
# ==========================================
@router_admin.get("/condominios/{id_condominio}/unidades", response_model=List[UnidadeResponse], summary="RF20 - Unidades do Condomínio")
def listar_unidades(id_condominio: int, incluir_inativas: bool = Query(False), db: Session = Depends(get_db)):
    _condominio_ou_404(db, id_condominio)
    return unidade_service.listar_unidades(db, id_condominio, incluir_inativas)

@router_admin.post("/condominios/{id_condominio}/unidades", response_model=UnidadeResponse, status_code=status.HTTP_201_CREATED, summary="RF20 - Cadastrar Unidade")
def cadastrar_unidade(id_condominio: int, dados: UnidadeCreate, db: Session = Depends(get_db)):
    return unidade_service.criar_unidade(db, id_condominio, dados)

@router_admin.put("/condominios/{id_condominio}/unidades/{id_unidade}", response_model=UnidadeResponse, summary="RF20 - Editar Unidade")
def editar_unidade(id_condominio: int, id_unidade: int, dados: UnidadeUpdate, db: Session = Depends(get_db)):
    unidade = unidade_service.editar_unidade(db, id_unidade, id_condominio, dados)
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")
    return unidade

@router_admin.patch("/condominios/{id_condominio}/unidades/{id_unidade}/inativar", response_model=UnidadeResponse, summary="RF20, RN17 - Inativar Unidade")
def inativar_unidade(id_condominio: int, id_unidade: int, db: Session = Depends(get_db)):
    unidade = unidade_service.inativar_unidade(db, id_unidade, id_condominio)
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")
    return unidade

# ==========================================
# SÍNDICOS E USUÁRIOS (RF13, RN07, RN12, RN13)
# ==========================================
@router_admin.post("/sindicos", response_model=SindicoCriadoResponse, status_code=status.HTTP_201_CREATED, summary="RF13 - Cadastro de Síndico")
def cadastrar_sindico(dados_sindico: SindicoCreate, db: Session = Depends(get_db)):
    """Gera a senha provisória e o link de validação (e-mail simulado no terminal e retornado na resposta)."""
    return admin_service.cadastrar_sindico(db, dados_sindico)

@router_admin.post("/sindicos/{id_usuario}/reenviar-validacao", response_model=SindicoCriadoResponse, summary="RN12 - Reenviar link de validação")
def reenviar_link_validacao(id_usuario: int, db: Session = Depends(get_db)):
    """Gera um novo link e uma nova senha provisória (os anteriores deixam de valer)."""
    return admin_service.reenviar_link_validacao(db, id_usuario)

@router_admin.patch("/usuarios/{id_usuario}/inativar", response_model=UsuarioResponse, summary="RN08 - Inativar Usuário")
def inativar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    try:
        return usuario_service.inativar_usuario(db, id_usuario)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router_admin.patch("/usuarios/{id_usuario}/reativar", response_model=UsuarioResponse, summary="Reativar Usuário")
def reativar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    try:
        return usuario_service.reativar_usuario(db, id_usuario)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
