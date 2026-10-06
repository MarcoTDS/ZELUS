from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from datetime import timedelta
from models.categoria import CategoriaDB
from models.condominio import CondominioDB
from schemas.categoria import CategoriaCreate, CategoriaUpdate

def converter_prazo(valor: int, unidade_prazo: str) -> timedelta:
    # RF08: Prazo de SLA informado em horas ou dias
    return timedelta(days=valor) if unidade_prazo == "dias" else timedelta(hours=valor)

def _verificar_nome_duplicado(db: Session, id_condominio: int, nome: str, ignorar_id: int = None):
    query = db.query(CategoriaDB).filter(
        CategoriaDB.id_condominio == id_condominio,
        CategoriaDB.ativo == True,
        func.lower(CategoriaDB.nome) == nome.lower()
    )
    if ignorar_id is not None:
        query = query.filter(CategoriaDB.id != ignorar_id)
    if query.first():
        raise HTTPException(status_code=409, detail="Já existe uma categoria ativa com este nome.")

def criar_categoria(db: Session, id_condominio: int, dados: CategoriaCreate):
    condominio = db.query(CondominioDB).filter(
        CondominioDB.id == id_condominio,
        CondominioDB.ativo == True
    ).first()
    if not condominio:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")

    _verificar_nome_duplicado(db, id_condominio, dados.nome)

    nova_categoria = CategoriaDB(
        nome=dados.nome,
        prazo_sla=converter_prazo(dados.prazo_sla, dados.unidade_prazo),
        id_condominio=id_condominio
    )
    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)
    return nova_categoria

def listar_categorias(db: Session, id_condominio: int, somente_ativas: bool = True):
    query = db.query(CategoriaDB).filter(CategoriaDB.id_condominio == id_condominio)

    if somente_ativas:
        query = query.filter(CategoriaDB.ativo == True)

    return query.order_by(CategoriaDB.nome).all()

def editar_categoria(db: Session, id_categoria: int, id_condominio: int, dados: CategoriaUpdate):
    # RN14: Apenas categorias do condomínio do síndico
    categoria = db.query(CategoriaDB).filter(
        CategoriaDB.id == id_categoria,
        CategoriaDB.id_condominio == id_condominio
    ).first()
    if not categoria:
        return None
        
    if dados.nome:
        _verificar_nome_duplicado(db, id_condominio, dados.nome, ignorar_id=categoria.id)
        categoria.nome = dados.nome
    if dados.prazo_sla:
        # RN01: Alterar o SLA não afeta chamados já abertos (eles guardam o prazo_sla_vigente)
        categoria.prazo_sla = converter_prazo(dados.prazo_sla, dados.unidade_prazo)
    if dados.ativo is not None:
        if dados.ativo:
            _verificar_nome_duplicado(db, id_condominio, categoria.nome, ignorar_id=categoria.id)
        categoria.ativo = dados.ativo
        
    db.commit()
    db.refresh(categoria)
    return categoria

def inativar_categoria(db: Session, id_categoria: int, id_condominio: int):
    categoria = db.query(CategoriaDB).filter(
        CategoriaDB.id == id_categoria,
        CategoriaDB.id_condominio == id_condominio
    ).first()
    if not categoria:
        return None

    categoria.ativo = False # Soft Delete (RN08)
    db.commit()
    db.refresh(categoria)
    return categoria
