from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.vinculo import VinculoCreate, VinculoAvaliar, VinculoResponse, VinculoPendenteResponse
from service import vinculo_service
from routers.dependencias import get_usuario_atual, get_sindico

router_vinculos = APIRouter(prefix="/vinculos", tags=["Vínculos de Moradores"])

@router_vinculos.post("/solicitar", response_model=VinculoResponse, status_code=status.HTTP_201_CREATED, summary="RF06 - Solicitar vínculo com outra unidade")
def solicitar_vinculo(dados: VinculoCreate, db: Session = Depends(get_db), usuario: dict = Depends(get_usuario_atual)):
    # Permitido também a moradores com cadastro pendente
    if usuario["perfil"] != "Morador":
        raise HTTPException(status_code=403, detail="Apenas moradores podem solicitar vínculo com unidades.")
    return vinculo_service.solicitar_vinculo(db, usuario["id"], dados)

@router_vinculos.get("/pendentes", response_model=List[VinculoPendenteResponse], summary="RF11 - Listar Cadastros Pendentes")
def listar_cadastros_pendentes(db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    return vinculo_service.listar_pendentes(db, usuario["id_condominio"])

@router_vinculos.patch("/{id_vinculo}/avaliar", response_model=VinculoResponse, summary="RF11 - Aprovar ou Rejeitar Cadastro")
def avaliar_cadastro(id_vinculo: int, dados: VinculoAvaliar, db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    """RN11 - Mesmo que a unidade já tenha responsável, o síndico pode "aprovar mesmo assim"."""
    vinculo = vinculo_service.avaliar_vinculo(db, id_vinculo, usuario["id_condominio"], dados.aprovado)
    if not vinculo:
        raise HTTPException(status_code=404, detail="Vínculo não encontrado.")
    return vinculo
