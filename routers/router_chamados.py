from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from schemas.chamado import ChamadoCreate, ChamadoCriadoComAviso, ChamadoResponse, ChamadoStatusUpdate, ChamadoDetalheResponse, HistoricoChamadoResponse
from service import chamado_service

# Dependência fictícia de autenticação (será implementada no router_auth)
def get_usuario_atual():
    return {"id": 1, "perfil": "Sindico", "id_condominio": 4}

router_chamados = APIRouter(prefix="/chamados", tags=["Chamados Help Desk"])

@router_chamados.post("/", response_model=ChamadoCriadoComAviso, status_code=status.HTTP_201_CREATED)
def abrir_chamado(
    chamado_dados: ChamadoCreate, 
    db: Session = Depends(get_db), 
    usuario=Depends(get_usuario_atual)
):
    """RF06, RN01, RN09 - O morador registra o chamado e herda o SLA da categoria."""
    if usuario["perfil"] != "Morador":
        raise HTTPException(status_code=403, detail="Apenas moradores podem abrir chamados.")
    
    # O service retorna {"chamado": ..., "aviso_similaridade": ...}, no formato de ChamadoCriadoComAviso
    return chamado_service.criar_chamado(db, chamado_dados, usuario["id"])

@router_chamados.get("/mural", response_model=List[ChamadoResponse])
def visualizar_mural(
    ticket: Optional[int] = Query(None, description="Busca por número do ticket"),
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_atual)
):
    """RF13, RN05 - Mural público (somente leitura) com os chamados do condomínio."""
    return chamado_service.listar_mural(db, usuario["id_condominio"], ticket)

@router_chamados.get("/worklist", response_model=List[ChamadoResponse])
def visualizar_worklist(
    ticket: Optional[int] = Query(None, description="Busca por número do ticket"),
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_atual)
):
    """RF09, RN04, RN14 - Fila do síndico, ordenada por urgência de SLA e restrita ao seu condomínio."""
    if usuario["perfil"] != "Sindico":
        raise HTTPException(status_code=403, detail="Acesso restrito a Síndicos.")
    
    return chamado_service.listar_worklist(db, usuario["id_condominio"], ticket)

@router_chamados.get("/{id_chamado}", response_model=ChamadoDetalheResponse)
def detalhar_chamado(
    id_chamado: int, 
    db: Session = Depends(get_db), 
    usuario=Depends(get_usuario_atual)
):
    """RN10 - Detalhes do chamado e registro automático de 'visto' pelo síndico."""
    chamado = chamado_service.obter_detalhe_chamado(db, id_chamado, usuario)
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")
    return chamado

@router_chamados.get("/{id_chamado}/historico", response_model=List[HistoricoChamadoResponse])
def listar_historico_chamado(
    id_chamado: int,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_atual)
):
    """RN03 - Linha do tempo das mudanças de status do chamado."""
    return chamado_service.listar_historico(db, id_chamado)

@router_chamados.patch("/{id_chamado}/status", response_model=ChamadoResponse)
def alterar_status_chamado(
    id_chamado: int, 
    atualizacao: ChamadoStatusUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_atual)
):
    """RF08, RN02, RN03, RN06 - Alteração de status pelo síndico com geração de histórico."""
    if usuario["perfil"] != "Sindico":
        raise HTTPException(status_code=403, detail="Apenas o síndico pode alterar o status.")
    
    return chamado_service.alterar_status(db, id_chamado, atualizacao.novo_status, atualizacao.observacao)