from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from datetime import datetime
from fastapi import HTTPException

from models.chamado import ChamadoDB, HistoricoChamadoDB
from models.categoria import CategoriaDB
from models.condominio import UnidadeDB
from models.enums import StatusChamadoEnum
from schemas.chamado import ChamadoCreate

STATUS_EM_ABERTO = [StatusChamadoEnum.Aberto, StatusChamadoEnum.Em_Andamento]
STATUS_FINALIZADOS = [StatusChamadoEnum.Resolvido, StatusChamadoEnum.Cancelado]

def _marcar_vencido(chamado: ChamadoDB, agora: datetime):
    # Adiciona a flag de "Vencido" dinamicamente (RN04)
    vencimento = chamado.data_abertura + chamado.prazo_sla_vigente
    chamado.vencido = agora > vencimento and chamado.status in STATUS_EM_ABERTO

def criar_chamado(db: Session, dados: ChamadoCreate, id_autor: int):
    unidade = db.query(UnidadeDB).filter(
        UnidadeDB.id == dados.id_unidade_destino,
        UnidadeDB.ativo == True
    ).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")

    categoria = db.query(CategoriaDB).filter(
        CategoriaDB.id == dados.id_categoria,
        CategoriaDB.ativo == True
    ).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")

    # A categoria precisa ser do mesmo condomínio da unidade
    if categoria.id_condominio != unidade.id_condominio:
        raise HTTPException(status_code=400, detail="A categoria informada não pertence ao condomínio da unidade.")

    # RN09: Verificar se já existe chamado aberto semelhante
    chamado_similar = db.query(ChamadoDB).filter(
        ChamadoDB.id_usuario_autor == id_autor,
        ChamadoDB.id_categoria == dados.id_categoria,
        ChamadoDB.id_unidade_destino == dados.id_unidade_destino,
        ChamadoDB.status.in_(STATUS_EM_ABERTO),
        ChamadoDB.ativo == True
    ).first()

    aviso = None
    if chamado_similar:
        aviso = "Aviso: Já existe um chamado em aberto para esta categoria e unidade."

    novo_chamado = ChamadoDB(
        id_usuario_autor=id_autor,
        id_unidade_destino=dados.id_unidade_destino,
        id_categoria=dados.id_categoria,
        status=StatusChamadoEnum.Aberto,
        titulo=dados.titulo,
        descricao=dados.descricao,
        foto_url=dados.foto_url,
        video_url=dados.video_url,
        prazo_sla_vigente=categoria.prazo_sla # RN01: SLA herdado da categoria no momento da abertura
    )
    db.add(novo_chamado)
    db.commit()
    db.refresh(novo_chamado)

    return {
        "chamado": novo_chamado,
        "aviso_similaridade": aviso
    }

def listar_mural(db: Session, id_condominio: int, ticket: int = None):
    # RN05, RN14: Apenas os chamados das unidades do condomínio
    query = db.query(ChamadoDB).join(UnidadeDB, ChamadoDB.id_unidade_destino == UnidadeDB.id).filter(
        UnidadeDB.id_condominio == id_condominio,
        ChamadoDB.ativo == True
    )
    
    if ticket:
        query = query.filter(ChamadoDB.id == ticket)

    chamados = query.order_by(desc(ChamadoDB.data_abertura)).all()

    agora = datetime.utcnow()
    for chamado in chamados:
        _marcar_vencido(chamado, agora)
        
    return chamados

def listar_worklist(db: Session, id_condominio: int, ticket: int = None):
    # RN14: Fila restrita ao condomínio do síndico
    query = db.query(ChamadoDB).join(UnidadeDB, ChamadoDB.id_unidade_destino == UnidadeDB.id).filter(
        UnidadeDB.id_condominio == id_condominio,
        ChamadoDB.ativo == True
    )
    
    if ticket:
        query = query.filter(ChamadoDB.id == ticket)
        
    # Ordena pela urgência (Data de Abertura + Prazo SLA Vigente)
    query = query.order_by(asc(ChamadoDB.data_abertura + ChamadoDB.prazo_sla_vigente))
    
    chamados = query.all()
    
    agora = datetime.utcnow()
    for chamado in chamados:
        _marcar_vencido(chamado, agora)
        
    return chamados

def obter_detalhe_chamado(db: Session, id_chamado: int, usuario: dict):
    chamado = db.query(ChamadoDB).filter(
        ChamadoDB.id == id_chamado, 
        ChamadoDB.ativo == True
    ).first()
    
    if not chamado:
        return None

    # RN10: Registra o 'visto' se o síndico abrir pela primeira vez
    if usuario["perfil"] == "Sindico" and chamado.data_visto is None:
        chamado.data_visto = datetime.utcnow()
        db.commit()
        db.refresh(chamado)

    _marcar_vencido(chamado, datetime.utcnow())

    return chamado

def listar_historico(db: Session, id_chamado: int):
    # RN03: Linha do tempo das mudanças de status do chamado
    return db.query(HistoricoChamadoDB).filter(
        HistoricoChamadoDB.id_chamado == id_chamado
    ).order_by(asc(HistoricoChamadoDB.data_alteracao)).all()

def alterar_status(db: Session, id_chamado: int, novo_status: StatusChamadoEnum, observacao: str):
    chamado = db.query(ChamadoDB).filter(
        ChamadoDB.id == id_chamado, 
        ChamadoDB.ativo == True
    ).first()

    novo_status = StatusChamadoEnum(novo_status)  # Converte para Enum, caso seja passado como string

    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")

    # RN06: Impede alteração de chamados finalizados
    if chamado.status in STATUS_FINALIZADOS:
        raise HTTPException(status_code=400, detail="Não é possível alterar o status de um chamado resolvido ou cancelado.")

    if chamado.status == novo_status:
        raise HTTPException(status_code=400, detail="O chamado já se encontra neste status.")

    status_anterior = chamado.status
    chamado.status = novo_status
    
    # RN03: Gera registro no histórico
    historico = HistoricoChamadoDB(
        id_chamado=chamado.id,
        status_anterior=status_anterior,
        novo_status=novo_status,
        observacao=observacao
    )
    
    db.add(historico)
    db.commit()
    db.refresh(chamado)

    _marcar_vencido(chamado, datetime.utcnow())
    
    return chamado