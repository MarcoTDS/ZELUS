from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from datetime import datetime
from fastapi import HTTPException

from models.chamado import ChamadoDB, HistoricoChamadoDB
from models.categoria import CategoriaDB
from models.condominio import UnidadeDB
from models.enums import StatusChamadoEnum, TipoUnidadeEnum
from schemas.chamado import ChamadoCreate
from service import vinculo_service

STATUS_EM_ABERTO = [StatusChamadoEnum.Aberto, StatusChamadoEnum.Em_Andamento]
STATUS_FINALIZADOS = [StatusChamadoEnum.Resolvido, StatusChamadoEnum.Cancelado]

# RN04: Faixas de urgência pela fração do prazo de SLA que ainda resta
LIMITE_URGENCIA_ALTA = 0.25   # restam 25% do prazo ou menos
LIMITE_URGENCIA_MEDIA = 0.50  # restam 50% do prazo ou menos

# ==========================================
# ATRIBUTOS CALCULADOS (não persistidos)
# ==========================================
def _calcular_prazo(chamado: ChamadoDB, agora: datetime):
    # RN04: "vencido" e "urgencia" (Vencido, Alta, Media, Baixa) definem a cor exibida nas telas
    vencimento = chamado.data_abertura + chamado.prazo_sla_vigente
    chamado.vencido = False
    chamado.urgencia = None
    chamado.data_conclusao = None
    chamado.concluido_no_prazo = None

    if chamado.status in STATUS_EM_ABERTO:
        restante = vencimento - agora
        fracao_restante = restante / chamado.prazo_sla_vigente
        if restante.total_seconds() < 0:
            chamado.vencido = True
            chamado.urgencia = "Vencido"
        elif fracao_restante <= LIMITE_URGENCIA_ALTA:
            chamado.urgencia = "Alta"
        elif fracao_restante <= LIMITE_URGENCIA_MEDIA:
            chamado.urgencia = "Media"
        else:
            chamado.urgencia = "Baixa"

    elif chamado.status == StatusChamadoEnum.Resolvido:
        # Tela de detalhe: "Concluído dentro do prazo"
        conclusao = next((h for h in reversed(chamado.historico) if h.novo_status == StatusChamadoEnum.Resolvido), None)
        if conclusao:
            chamado.data_conclusao = conclusao.data_alteracao
            chamado.concluido_no_prazo = conclusao.data_alteracao <= vencimento

def _preparar_lista(chamados):
    agora = datetime.utcnow()
    for chamado in chamados:
        _calcular_prazo(chamado, agora)
    return chamados

def _query_condominio(db: Session, id_condominio: int):
    # RN14: Apenas os chamados das unidades do condomínio
    return db.query(ChamadoDB).join(UnidadeDB, ChamadoDB.id_unidade_destino == UnidadeDB.id).filter(
        UnidadeDB.id_condominio == id_condominio,
        ChamadoDB.ativo == True
    )

# ==========================================
# ABERTURA (RF07, RN01, RN05, RN09)
# ==========================================
def criar_chamado(db: Session, dados: ChamadoCreate, id_autor: int, id_condominio: int):
    unidade = db.query(UnidadeDB).filter(
        UnidadeDB.id == dados.id_unidade_destino,
        UnidadeDB.ativo == True
    ).first()
    if not unidade or unidade.id_condominio != id_condominio:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")

    # RN05: O morador só abre chamados para as suas unidades aprovadas ou para áreas comuns
    if unidade.tipo_unidade != TipoUnidadeEnum.Area_Comum:
        unidades_do_morador = [u.id for u in vinculo_service.listar_unidades_do_morador(db, id_autor)]
        if unidade.id not in unidades_do_morador:
            raise HTTPException(status_code=403, detail="Você só pode abrir chamados para as suas unidades ou para áreas comuns.")

    categoria = db.query(CategoriaDB).filter(
        CategoriaDB.id == dados.id_categoria,
        CategoriaDB.id_condominio == id_condominio,
        CategoriaDB.ativo == True
    ).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")

    # RN09: Verificar se já existe chamado aberto semelhante (avisa, mas não bloqueia)
    chamado_similar = db.query(ChamadoDB).filter(
        ChamadoDB.id_usuario_autor == id_autor,
        ChamadoDB.id_categoria == dados.id_categoria,
        ChamadoDB.id_unidade_destino == dados.id_unidade_destino,
        ChamadoDB.status.in_(STATUS_EM_ABERTO),
        ChamadoDB.ativo == True
    ).first()

    aviso = None
    if chamado_similar:
        aviso = f"Já existe um chamado aberto com esta categoria para esta unidade (#{chamado_similar.id:04d})."

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
    _calcular_prazo(novo_chamado, datetime.utcnow())

    return {
        "chamado": novo_chamado,
        "aviso_similaridade": aviso
    }

def verificar_similaridade(db: Session, id_autor: int, id_categoria: int, id_unidade: int):
    # RN09: Permite ao front exibir o aviso enquanto o morador preenche o formulário
    return db.query(ChamadoDB).filter(
        ChamadoDB.id_usuario_autor == id_autor,
        ChamadoDB.id_categoria == id_categoria,
        ChamadoDB.id_unidade_destino == id_unidade,
        ChamadoDB.status.in_(STATUS_EM_ABERTO),
        ChamadoDB.ativo == True
    ).first()

# ==========================================
# LISTAGENS (RF10, RF14, RF17, RF22)
# ==========================================
def listar_meus_chamados(db: Session, id_autor: int, ticket: int = None):
    # RF14: Dashboard do Morador - "Meus Chamados"
    query = db.query(ChamadoDB).filter(
        ChamadoDB.id_usuario_autor == id_autor,
        ChamadoDB.ativo == True
    )
    if ticket:
        query = query.filter(ChamadoDB.id == ticket)

    return _preparar_lista(query.order_by(desc(ChamadoDB.data_abertura)).all())

def listar_mural(db: Session, id_condominio: int, ticket: int = None):
    # RF17, RN05: Mural público (somente leitura) com todos os chamados do condomínio
    query = _query_condominio(db, id_condominio)
    if ticket:
        query = query.filter(ChamadoDB.id == ticket)

    return _preparar_lista(query.order_by(desc(ChamadoDB.data_abertura)).all())

def listar_worklist(db: Session, id_condominio: int, ticket: int = None, status: StatusChamadoEnum = None):
    # RF10: Fila do síndico com os chamados em aberto, ordenada por urgência (vencimento mais próximo primeiro)
    query = _query_condominio(db, id_condominio).filter(ChamadoDB.status.in_(STATUS_EM_ABERTO))

    if ticket:
        query = query.filter(ChamadoDB.id == ticket)
    if status:
        query = query.filter(ChamadoDB.status == status)
        
    query = query.order_by(asc(ChamadoDB.data_abertura + ChamadoDB.prazo_sla_vigente))
    return _preparar_lista(query.all())

def listar_historico_condominio(db: Session, id_condominio: int, ticket: int = None, status: StatusChamadoEnum = None):
    # RF22: Todos os chamados do condomínio, inclusive resolvidos e cancelados
    query = _query_condominio(db, id_condominio)

    if ticket:
        query = query.filter(ChamadoDB.id == ticket)
    if status:
        query = query.filter(ChamadoDB.status == status)

    return _preparar_lista(query.order_by(desc(ChamadoDB.data_abertura)).all())

def obter_resumo(db: Session, id_condominio: int):
    # RF03: Resumo do Dashboard do Síndico
    em_aberto = listar_worklist(db, id_condominio)
    return {
        "abertos": len(em_aberto),
        "urgentes": sum(1 for c in em_aberto if c.urgencia in ("Vencido", "Alta")),
        "vencidos": sum(1 for c in em_aberto if c.vencido)
    }

# ==========================================
# DETALHE E STATUS (RF09, RF18, RN02, RN03, RN06, RN10)
# ==========================================
def obter_detalhe_chamado(db: Session, id_chamado: int, usuario: dict):
    chamado = _query_condominio(db, usuario["id_condominio"]).filter(ChamadoDB.id == id_chamado).first()
    if not chamado:
        return None

    # RN10: Registra o 'visto' se o síndico abrir pela primeira vez
    if usuario["perfil"] == "Sindico" and chamado.data_visto is None:
        chamado.data_visto = datetime.utcnow()
        db.commit()
        db.refresh(chamado)

    _calcular_prazo(chamado, datetime.utcnow())
    return chamado

def listar_historico(db: Session, id_chamado: int, id_condominio: int):
    # RN03: Linha do tempo das mudanças de status do chamado
    if not _query_condominio(db, id_condominio).filter(ChamadoDB.id == id_chamado).first():
        return None

    return db.query(HistoricoChamadoDB).filter(
        HistoricoChamadoDB.id_chamado == id_chamado
    ).order_by(asc(HistoricoChamadoDB.data_alteracao)).all()

def alterar_status(db: Session, id_chamado: int, id_condominio: int, novo_status: StatusChamadoEnum, observacao: str):
    chamado = _query_condominio(db, id_condominio).filter(ChamadoDB.id == id_chamado).first()

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

    _calcular_prazo(chamado, datetime.utcnow())
    return chamado
