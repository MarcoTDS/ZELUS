from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.usuario import EditarPerfilRequest, UsuarioResponse
from schemas.vinculo import MoradorResponse
from service import vinculo_service, usuario_service
from routers.dependencias import get_sindico

router_moradores = APIRouter(prefix="/moradores", tags=["Gerenciamento de Moradores"])

def _validar_morador_do_condominio(db: Session, id_usuario: int, usuario: dict):
    # RN14: O síndico só gerencia moradores do próprio condomínio
    if not vinculo_service.morador_pertence_ao_condominio(db, id_usuario, usuario["id_condominio"]):
        raise HTTPException(status_code=404, detail="Morador não encontrado.")

@router_moradores.get("/", response_model=List[MoradorResponse], summary="RF21 - Moradores do Condomínio")
def listar_moradores(db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    """Inclui moradores inativados (exibidos como "Inativo", com opção de reativar)."""
    return vinculo_service.listar_moradores(db, usuario["id_condominio"])

@router_moradores.put("/{id_usuario}", response_model=UsuarioResponse, summary="RF21 - Editar Morador")
def editar_morador(id_usuario: int, dados: EditarPerfilRequest, db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    _validar_morador_do_condominio(db, id_usuario, usuario)
    try:
        return usuario_service.atualizar_perfil(db, id_usuario, dados.nome, dados.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router_moradores.patch("/{id_usuario}/inativar", response_model=UsuarioResponse, summary="RF21 - Inativar Morador")
def inativar_morador(id_usuario: int, db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    _validar_morador_do_condominio(db, id_usuario, usuario)
    return usuario_service.inativar_usuario(db, id_usuario)

@router_moradores.patch("/{id_usuario}/reativar", response_model=UsuarioResponse, summary="RF21 - Reativar Morador")
def reativar_morador(id_usuario: int, db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    _validar_morador_do_condominio(db, id_usuario, usuario)
    return usuario_service.reativar_usuario(db, id_usuario)
