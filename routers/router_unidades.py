from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas.unidade import UnidadeCreate, UnidadeUpdate, UnidadeResponse, UnidadeResumo
from service import unidade_service
from routers.dependencias import get_sindico, get_morador

router_unidades = APIRouter(prefix="/unidades", tags=["Unidades"])

@router_unidades.get("/para-chamado", response_model=List[UnidadeResumo], summary="RF07, RN05 - Unidades para abrir chamado")
def listar_unidades_para_chamado(db: Session = Depends(get_db), usuario: dict = Depends(get_morador)):
    """Unidades aprovadas do morador + áreas comuns do condomínio (dropdown "Unidade" da Tela de Novo Chamado)."""
    return unidade_service.listar_unidades_para_chamado(db, usuario["id"], usuario["id_condominio"])

@router_unidades.get("/", response_model=List[UnidadeResponse], summary="RF20 - Unidades do Condomínio")
def listar_unidades(incluir_inativas: bool = Query(False), db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    return unidade_service.listar_unidades(db, usuario["id_condominio"], incluir_inativas)

@router_unidades.post("/", response_model=UnidadeResponse, status_code=status.HTTP_201_CREATED, summary="RF20 - Cadastrar Unidade")
def cadastrar_unidade(dados: UnidadeCreate, db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    return unidade_service.criar_unidade(db, usuario["id_condominio"], dados)

@router_unidades.put("/{id_unidade}", response_model=UnidadeResponse, summary="RF20 - Editar Unidade")
def editar_unidade(id_unidade: int, dados: UnidadeUpdate, db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    unidade = unidade_service.editar_unidade(db, id_unidade, usuario["id_condominio"], dados)
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")
    return unidade

@router_unidades.patch("/{id_unidade}/inativar", response_model=UnidadeResponse, summary="RF20, RN17 - Inativar Unidade")
def inativar_unidade(id_unidade: int, db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    unidade = unidade_service.inativar_unidade(db, id_unidade, usuario["id_condominio"])
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")
    return unidade
