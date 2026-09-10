from sqlalchemy.orm import Session
from sqlalchemy import asc
from datetime import datetime
from fastapi import HTTPException

from models.chamado import ChamadoDB, HistoricoChamadoDB
from models.enums import StatusChamadoEnum
from schemas.chamado import ChamadoCreate

def criar_chamado(db: Session, dados: ChamadoCreate, id_autor: int):
    # RN09: Verificar se já existe chamado aberto semelhante
    chamado_similar = db.query(ChamadoDB).filter(
        ChamadoDB.id_usuario_autor == id_autor,
        ChamadoDB.id_categoria == dados.id_categoria,
        ChamadoDB.id_unidade_destino == dados.id_unidade_destino,
        ChamadoDB.status.in_([StatusChamadoEnum.Aberto, StatusChamadoEnum.Em_Andamento]),
        ChamadoDB.excluido_logicamente == False
    ).first()

    aviso = None
    if chamado_similar:
        aviso = "Aviso: Já existe um chamado em aberto para esta categoria e unidade."

    # Simulação de busca da categoria para herdar o SLA (RN01)
    # categoria = db.query(CategoriaDB).filter(CategoriaDB.id == dados.id_categoria).first()
    # prazo_vigente = categoria.prazo_sla 
    from datetime import timedelta
    prazo_vigente = timedelta(hours=48) 

    novo_chamado = ChamadoDB(
        id_usuario_autor=id_autor,
        id_unidade_destino=dados.id_unidade_destino,
        id_categoria=dados.id_categoria,
        status=StatusChamadoEnum.Aberto,
        titulo=dados.titulo,
        descricao=dados.descricao,
        foto_url=dados.foto_url,
        video_url=dados.video_url,
        prazo_sla_vigente=prazo_vigente
    )
    db.add(novo_chamado)
    db.commit()
    db.refresh(novo_chamado)

    return {
        "chamado": novo_chamado,
        "aviso_similaridade": aviso
    }

def listar_mural(db: Session, id_condominio: int, ticket: int = None):
    query = db.query(ChamadoDB).filter(ChamadoDB.excluido_logicamente == False)
    # A junção com Unidade/Condomínio seria necessária aqui para filtrar pelo id_condominio (RN14, RN05)
    
    if ticket:
        query = query.filter(ChamadoDB.id == ticket)
        
    return query.all()

def listar_worklist(db: Session, id_condominio: int, ticket: int = None):
    query = db.query(ChamadoDB).filter(ChamadoDB.excluido_logicamente == False)
    
    if ticket:
        query = query.filter(ChamadoDB.id == ticket)
        
    # Ordena pela urgência (Data de Abertura + Prazo SLA Vigente)
    query = query.order_by(asc(ChamadoDB.data_abertura + ChamadoDB.prazo_sla_vigente))
    
    chamados = query.all()
    
    # Adiciona a flag de "Vencido" dinamicamente (RN04)
    agora = datetime.utcnow()
    for chamado in chamados:
        vencimento = chamado.data_abertura + chamado.prazo_sla_vigente
        chamado.vencido = (
            agora > vencimento 
            and chamado.status in [StatusChamadoEnum.Aberto, StatusChamadoEnum.Em_Andamento]
        )
        
    return chamados

def obter_detalhe_chamado(db: Session, id_chamado: int, usuario: dict):
    chamado = db.query(ChamadoDB).filter(
        ChamadoDB.id == id_chamado, 
        ChamadoDB.excluido_logicamente == False
    ).first()
    
    if not chamado:
        return None

    # RN10: Registra o 'visto' se o síndico abrir pela primeira vez
    if usuario["perfil"] == "Sindico" and chamado.data_visto is None:
        chamado.data_visto = datetime.utcnow()
        db.commit()
        db.refresh(chamado)

    return chamado

def alterar_status(db: Session, id_chamado: int, novo_status: StatusChamadoEnum, observacao: str):
    chamado = db.query(ChamadoDB).filter(
        ChamadoDB.id == id_chamado, 
        ChamadoDB.excluido_logicamente == False
    ).first()

    novo_status = StatusChamadoEnum(novo_status)  # Converte para Enum, caso seja passado como string

    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")

    # RN06: Impede alteração de chamados finalizados
    if chamado.status in [StatusChamadoEnum.Resolvido, StatusChamadoEnum.Cancelado]:
        raise HTTPException(status_code=400, detail="Não é possível alterar o status de um chamado resolvido ou cancelado.")

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
    
    return chamado