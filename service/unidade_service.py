from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.condominio import CondominioDB, UnidadeDB
from models.chamado import ChamadoDB
from models.enums import TipoUnidadeEnum
from schemas.unidade import UnidadeCreate, UnidadeUpdate
from service import vinculo_service

CAMPOS_UNIDADE = ["bloco", "apartamento", "rua", "numero_casa", "descricao"]

def validar_unidade(tipo_unidade: TipoUnidadeEnum, unidade):
    # Espelha a CHECK constraint "ck_unidade_identificacao" do banco
    if tipo_unidade == TipoUnidadeEnum.Apartamento and not unidade.apartamento:
        raise HTTPException(status_code=400, detail="Unidades do tipo Apartamento exigem o número do apartamento.")
    if tipo_unidade == TipoUnidadeEnum.Casa and not unidade.numero_casa:
        raise HTTPException(status_code=400, detail="Unidades do tipo Casa exigem o número da casa.")
    if tipo_unidade == TipoUnidadeEnum.Area_Comum and not unidade.descricao:
        raise HTTPException(status_code=400, detail="Áreas comuns exigem uma descrição (ex: Garagem).")

def _verificar_duplicidade(db: Session, id_condominio: int, unidade: UnidadeDB):
    # Impede duas unidades ativas com a mesma identificação no condomínio (ex: dois "Bloco A, Apto 21")
    existentes = db.query(UnidadeDB).filter(
        UnidadeDB.id_condominio == id_condominio,
        UnidadeDB.ativo == True,
        UnidadeDB.id != unidade.id
    ).all()
    identificacao = unidade.identificacao.lower()
    if any(u.identificacao.lower() == identificacao for u in existentes):
        raise HTTPException(status_code=409, detail=f"Já existe a unidade '{unidade.identificacao}' neste condomínio.")

def _buscar_condominio_ativo(db: Session, id_condominio: int):
    condominio = db.query(CondominioDB).filter(
        CondominioDB.id == id_condominio,
        CondominioDB.ativo == True
    ).first()
    if not condominio:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")
    return condominio

def montar_unidade(id_condominio: int, dados) -> UnidadeDB:
    validar_unidade(dados.tipo_unidade, dados)
    return UnidadeDB(
        id_condominio=id_condominio,
        tipo_unidade=dados.tipo_unidade,
        **{campo: getattr(dados, campo) for campo in CAMPOS_UNIDADE}
    )

# ==========================================
# CONSULTAS
# ==========================================
def buscar_unidade(db: Session, id_unidade: int, id_condominio: int = None):
    # Com id_condominio, retorna apenas unidades daquele condomínio (RN14)
    query = db.query(UnidadeDB).filter(UnidadeDB.id == id_unidade)
    if id_condominio is not None:
        query = query.filter(UnidadeDB.id_condominio == id_condominio)
    return query.first()

def listar_unidades(db: Session, id_condominio: int, incluir_inativas: bool = False, incluir_areas_comuns: bool = True):
    query = db.query(UnidadeDB).filter(UnidadeDB.id_condominio == id_condominio)

    if not incluir_inativas:
        query = query.filter(UnidadeDB.ativo == True)
    if not incluir_areas_comuns:
        query = query.filter(UnidadeDB.tipo_unidade != TipoUnidadeEnum.Area_Comum)

    unidades = query.order_by(UnidadeDB.tipo_unidade, UnidadeDB.bloco, UnidadeDB.apartamento, UnidadeDB.rua, UnidadeDB.numero_casa, UnidadeDB.descricao).all()

    # RN17: Indica se a unidade tem morador responsável (a lixeira fica desabilitada na tela)
    for unidade in unidades:
        responsavel = vinculo_service.obter_responsavel_unidade(db, unidade.id)
        unidade.responsavel = responsavel.nome if responsavel else None

    return unidades

def listar_unidades_para_cadastro(db: Session, id_condominio: int):
    # RF06: Unidades exibidas na tela de cadastro do morador (sem áreas comuns)
    _buscar_condominio_ativo(db, id_condominio)
    return listar_unidades(db, id_condominio, incluir_areas_comuns=False)

def listar_unidades_para_chamado(db: Session, id_usuario: int, id_condominio: int):
    # RN05: O morador abre chamados para as suas unidades aprovadas ou para as áreas comuns do condomínio
    proprias = vinculo_service.listar_unidades_do_morador(db, id_usuario)
    areas_comuns = db.query(UnidadeDB).filter(
        UnidadeDB.id_condominio == id_condominio,
        UnidadeDB.tipo_unidade == TipoUnidadeEnum.Area_Comum,
        UnidadeDB.ativo == True
    ).order_by(UnidadeDB.descricao).all()
    return proprias + areas_comuns

# ==========================================
# CADASTRO, EDIÇÃO E INATIVAÇÃO (RF20, RN17)
# ==========================================
def criar_unidade(db: Session, id_condominio: int, dados: UnidadeCreate):
    _buscar_condominio_ativo(db, id_condominio)

    nova_unidade = montar_unidade(id_condominio, dados)
    _verificar_duplicidade(db, id_condominio, nova_unidade)

    db.add(nova_unidade)
    db.commit()
    db.refresh(nova_unidade)
    return nova_unidade

def editar_unidade(db: Session, id_unidade: int, id_condominio: int, dados: UnidadeUpdate):
    unidade = buscar_unidade(db, id_unidade, id_condominio)
    if not unidade or not unidade.ativo:
        return None

    if dados.tipo_unidade is not None:
        unidade.tipo_unidade = dados.tipo_unidade
    for campo in CAMPOS_UNIDADE:
        if campo in dados.model_fields_set: # Apenas os campos enviados (permite limpar com null)
            setattr(unidade, campo, getattr(dados, campo))

    validar_unidade(unidade.tipo_unidade, unidade)
    _verificar_duplicidade(db, id_condominio, unidade)

    db.commit()
    db.refresh(unidade)
    return unidade

def inativar_unidade(db: Session, id_unidade: int, id_condominio: int):
    unidade = buscar_unidade(db, id_unidade, id_condominio)
    if not unidade or not unidade.ativo:
        return None

    # RN17: Unidade com morador responsável vinculado não pode ser removida
    responsavel = vinculo_service.obter_responsavel_unidade(db, unidade.id)
    if responsavel:
        raise HTTPException(status_code=400, detail=f"A unidade possui um morador responsável vinculado ({responsavel.nome}).")

    unidade.ativo = False # Soft Delete (RN08)
    db.commit()
    db.refresh(unidade)
    return unidade

def unidade_possui_chamados(db: Session, id_unidade: int) -> bool:
    return db.query(ChamadoDB).filter(ChamadoDB.id_unidade_destino == id_unidade).first() is not None
