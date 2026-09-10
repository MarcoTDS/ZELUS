from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.categoria import CategoriaCreate, CategoriaUpdate
from service import categoria_service

def get_usuario_atual():
    # Placeholder: simula um Síndico logado
    return {"id": 1, "perfil": "Sindico", "id_condominio": 1}

router_categorias = APIRouter(prefix="/categorias", tags=["Categorias e SLA"])

@router_categorias.post("/", status_code=status.HTTP_201_CREATED, summary="RF07 - Cadastrar Categoria")
def cadastrar_categoria(dados: CategoriaCreate, db: Session = Depends(get_db), usuario = Depends(get_usuario_atual)):
    if usuario["perfil"] != "Sindico":
        raise HTTPException(status_code=403, detail="Apenas síndicos podem criar categorias.")
    return categoria_service.criar_categoria(db, dados)

@router_categorias.put("/{id_categoria}", summary="RF07 - Editar ou Inativar Categoria")
def editar_categoria(id_categoria: int, dados: CategoriaUpdate, db: Session = Depends(get_db), usuario = Depends(get_usuario_atual)):
    if usuario["perfil"] != "Sindico":
        raise HTTPException(status_code=403, detail="Apenas síndicos podem editar categorias.")
    
    categoria = categoria_service.editar_categoria(db, id_categoria, dados)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return {"mensagem": "Categoria atualizada com sucesso"}