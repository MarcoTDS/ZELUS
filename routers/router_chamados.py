from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models.enums import StatusChamadoEnum
from schemas.chamado import (ChamadoCreate, ChamadoCriadoComAviso, ChamadoResponse, ChamadoStatusUpdate, ChamadoDetalheResponse,
                             HistoricoChamadoResponse, SimilaridadeResponse, ResumoSindicoResponse)
from service import chamado_service
from routers.dependencias import get_morador, get_sindico, get_morador_ou_sindico

router_chamados = APIRouter(prefix="/chamados", tags=["Chamados Help Desk"])

FILTRO_TICKET = Query(None, description="Busca por número do ticket")

# ==========================================
# MORADOR
# ==========================================
@router_chamados.post("/", response_model=ChamadoCriadoComAviso, status_code=status.HTTP_201_CREATED, summary="RF07 - Abrir Chamado")
def abrir_chamado(chamado_dados: ChamadoCreate, db: Session = Depends(get_db), usuario: dict = Depends(get_morador)):
    """RF07, RN01, RN05, RN09 - O morador registra o chamado e herda o SLA da categoria."""
    return chamado_service.criar_chamado(db, chamado_dados, usuario["id"], usuario["id_condominio"])

@router_chamados.get("/similaridade", response_model=SimilaridadeResponse, summary="RN09 - Verificar chamado semelhante")
def verificar_similaridade(id_categoria: int, id_unidade: int, db: Session = Depends(get_db), usuario: dict = Depends(get_morador)):
    """Permite exibir o aviso na Tela de Novo Chamado antes do envio."""
    similar = chamado_service.verificar_similaridade(db, usuario["id"], id_categoria, id_unidade)
    return {"existe_similar": similar is not None, "id_chamado": similar.id if similar else None}

@router_chamados.get("/meus", response_model=List[ChamadoResponse], summary="RF14 - Meus Chamados")
def listar_meus_chamados(ticket: Optional[int] = FILTRO_TICKET, db: Session = Depends(get_db), usuario: dict = Depends(get_morador)):
    return chamado_service.listar_meus_chamados(db, usuario["id"], ticket)

@router_chamados.get("/mural", response_model=List[ChamadoResponse], summary="RF17 - Mural do Condomínio")
def visualizar_mural(ticket: Optional[int] = FILTRO_TICKET, db: Session = Depends(get_db), usuario: dict = Depends(get_morador_ou_sindico)):
    """RF17, RN05 - Mural público (somente leitura) com os chamados do condomínio."""
    return chamado_service.listar_mural(db, usuario["id_condominio"], ticket)

# ==========================================
# SÍNDICO
# ==========================================
@router_chamados.get("/worklist", response_model=List[ChamadoResponse], summary="RF10 - Fila de Chamados")
def visualizar_worklist(
    ticket: Optional[int] = FILTRO_TICKET,
    status_chamado: Optional[StatusChamadoEnum] = Query(None, alias="status", description="Filtro: Aberto ou Em Andamento"),
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_sindico)
):
    """RF10, RN04, RN14 - Chamados em aberto, ordenados por urgência de SLA."""
    return chamado_service.listar_worklist(db, usuario["id_condominio"], ticket, status_chamado)

@router_chamados.get("/historico", response_model=List[ChamadoResponse], summary="RF22 - Histórico de Chamados")
def visualizar_historico_condominio(
    ticket: Optional[int] = FILTRO_TICKET,
    status_chamado: Optional[StatusChamadoEnum] = Query(None, alias="status", description="Filtro por status"),
    db: Session = Depends(get_db),
    usuario: dict = Depends(get_sindico)
):
    """RF22 - Todos os chamados do condomínio, inclusive resolvidos e cancelados."""
    return chamado_service.listar_historico_condominio(db, usuario["id_condominio"], ticket, status_chamado)

@router_chamados.get("/resumo", response_model=ResumoSindicoResponse, summary="RF03 - Resumo do Dashboard do Síndico")
def obter_resumo(db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    return chamado_service.obter_resumo(db, usuario["id_condominio"])

@router_chamados.patch("/{id_chamado}/status", response_model=ChamadoResponse, summary="RF09 - Alterar Status")
def alterar_status_chamado(id_chamado: int, atualizacao: ChamadoStatusUpdate, db: Session = Depends(get_db), usuario: dict = Depends(get_sindico)):
    """RF09, RN02, RN03, RN06 - Alteração de status pelo síndico com geração de histórico."""
    return chamado_service.alterar_status(db, id_chamado, usuario["id_condominio"], atualizacao.novo_status, atualizacao.observacao)

# ==========================================
# MORADOR E SÍNDICO
# ==========================================
@router_chamados.get("/{id_chamado}", response_model=ChamadoDetalheResponse, summary="RF18 - Detalhes do Chamado")
def detalhar_chamado(id_chamado: int, db: Session = Depends(get_db), usuario: dict = Depends(get_morador_ou_sindico)):
    """RF18, RN10 - Detalhes do chamado e registro automático de 'visto' pelo síndico."""
    chamado = chamado_service.obter_detalhe_chamado(db, id_chamado, usuario)
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")
    return chamado

@router_chamados.get("/{id_chamado}/historico", response_model=List[HistoricoChamadoResponse], summary="RN03 - Histórico de Status do Chamado")
def listar_historico_chamado(id_chamado: int, db: Session = Depends(get_db), usuario: dict = Depends(get_morador_ou_sindico)):
    historico = chamado_service.listar_historico(db, id_chamado, usuario["id_condominio"])
    if historico is None:
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")
    return historico
