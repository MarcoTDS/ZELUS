from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas.admin import CondominioPublicoResponse
from schemas.unidade import UnidadeResumo
from service import admin_service, unidade_service

router_publico = APIRouter(prefix="/publico", tags=["Público (Tela de Cadastro)"])

@router_publico.get("/condominios", response_model=List[CondominioPublicoResponse], summary="RF06 - Condomínios disponíveis no cadastro")
def listar_condominios(db: Session = Depends(get_db)):
    return admin_service.listar_condominios(db)

@router_publico.get("/condominios/{id_condominio}/unidades", response_model=List[UnidadeResumo], summary="RF06 - Unidades disponíveis no cadastro")
def listar_unidades(id_condominio: int, db: Session = Depends(get_db)):
    """Lista as unidades do condomínio (sem as áreas comuns) para o morador escolher no cadastro."""
    return unidade_service.listar_unidades_para_cadastro(db, id_condominio)
