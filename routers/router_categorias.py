from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.categoria import CategoriaCreate, CategoriaUpdate, CategoriaResponse
from service import categoria_service

def get_usuario_atual():
    # Placeholder: simula um Síndico logado
    return {"id": 1, "perfil": "Sindico", "id_condominio": 1}

router_categorias = APIRouter(prefix="/categorias", tags=["Categorias e SLA"])

@router_categorias.get("/", response_model=List[CategoriaResponse], summary="RF07 - Listar Categorias do Condomínio")
def listar_categorias(
    incluir_inativas: bool = Query(False, description="Apenas para síndicos: inclui categorias inativadas"),
    db: Session = Depends(get_db),
    usuario = Depends(get_usuario_atual)
):
    # Moradores enxergam apenas as categorias ativas (usadas na abertura de chamados)
    somente_ativas = not (incluir_inativas and usuario["perfil"] == "Sindico")
    return categoria_service.listar_categorias(db, usuario["id_condominio"], somente_ativas)

@router_categorias.post("/", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED, summary="RF07 - Cadastrar Categoria")
def cadastrar_categoria(dados: CategoriaCreate, db: Session = Depends(get_db), usuario = Depends(get_usuario_atual)):
    if usuario["perfil"] != "Sindico":
        raise HTTPException(status_code=403, detail="Apenas síndicos podem criar categorias.")
    if dados.id_condominio != usuario["id_condominio"]:
        raise HTTPException(status_code=403, detail="O síndico só pode criar categorias para o próprio condomínio.")
    return categoria_service.criar_categoria(db, dados)

@router_categorias.put("/{id_categoria}", response_model=CategoriaResponse, summary="RF07 - Editar ou Inativar Categoria")
def editar_categoria(id_categoria: int, dados: CategoriaUpdate, db: Session = Depends(get_db), usuario = Depends(get_usuario_atual)):
    if usuario["perfil"] != "Sindico":
        raise HTTPException(status_code=403, detail="Apenas síndicos podem editar categorias.")
    
    categoria = categoria_service.editar_categoria(db, id_categoria, dados)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return categoria