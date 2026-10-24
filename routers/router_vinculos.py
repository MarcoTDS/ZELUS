from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas.vinculo import VinculoCreate, VinculoAvaliar, VinculoResponse, VinculoPendenteResponse
from service import vinculo_service
from routers.dependencias import get_usuario_atual, get_sindico, get_morador

router_vinculos = APIRouter(prefix="/vinculos", tags=["Vínculos de Moradores"])

@router_vinculos.post("/solicitar", response_model=VinculoResponse, status_code=status.HTTP_201_CREATED, summary="RF06 - Solicitar vínculo com outra unidade")
def solicitar_vinculo(dados: VinculoCreate, db: Session = Depends(get_db), usuario: dict = Depends(get_usuario_atual)):
    # Permitido também a moradores com cadastro pendente
    if usuario["perfil"] != "Morador":
        raise HTTPException(status_code=403, detail="Apenas moradores podem solicitar vínculo com unidades.")
    return vinculo_service.solicitar_vinculo(db, usuario["id"], dados)

@router_vinculos.get("/meus", response_model=List[VinculoResponse], summary="RF06 - Minhas unidades (morador)")
def listar_meus_vinculos(db: Session = Depends(get_db), usuario: dict = Depends(get_morador)):
    return vinculo_service.listar_vinculos_do_morador(db, usuario["id"])

@router_vinculos.patch("/{id_vinculo}/encerrar", response_model=VinculoResponse, summary="RF06 - Sair da unidade ou cancelar solicitação (morador)")
def encerrar_meu_vinculo(id_vinculo: int, db: Session = Depends(get_db), usuario: dict = Depends(get_morador)):
    """A última unidade aprovada não pode ser encerrada pelo morador (a saída do condomínio é feita pelo síndico)."""
    vinculo = vinculo_service.encerrar_vinculo_do_morador(db, id_vinculo, usuario["id"])
    if not vinculo:
        raise HTTPException(status_code=404, detail="Vínculo não encontrado.")
    return vinculo

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
