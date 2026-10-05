from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import timedelta
from models.categoria import CategoriaDB
from models.condominio import CondominioDB
from schemas.categoria import CategoriaCreate, CategoriaUpdate

def criar_categoria(db: Session, dados: CategoriaCreate):
    condominio = db.query(CondominioDB).filter(
        CondominioDB.id == dados.id_condominio,
        CondominioDB.ativo == True
    ).first()
    if not condominio:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")

    nova_categoria = CategoriaDB(
        nome=dados.nome,
        prazo_sla=timedelta(hours=dados.prazo_sla_horas),
        id_condominio=dados.id_condominio
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

def editar_categoria(db: Session, id_categoria: int, dados: CategoriaUpdate):
    categoria = db.query(CategoriaDB).filter(CategoriaDB.id == id_categoria).first()
    if not categoria:
        return None
        
    if dados.nome:
        categoria.nome = dados.nome
    if dados.prazo_sla_horas:
        categoria.prazo_sla = timedelta(hours=dados.prazo_sla_horas)
    if dados.ativo is not None:
        categoria.ativo = dados.ativo
        
    db.commit()
    db.refresh(categoria)
    return categoria