from sqlalchemy.orm import Session
from datetime import timedelta
from models.categoria import CategoriaDB
from schemas.categoria import CategoriaCreate, CategoriaUpdate

def criar_categoria(db: Session, dados: CategoriaCreate):
    nova_categoria = CategoriaDB(
        nome=dados.nome,
        prazo_sla=timedelta(hours=dados.prazo_sla_horas),
        id_condominio=dados.id_condominio
    )
    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)
    return nova_categoria

def editar_categoria(db: Session, id_categoria: int, dados: CategoriaUpdate):
    categoria = db.query(CategoriaDB).filter(CategoriaDB.id == id_categoria).first()
    if not categoria:
        return None
        
    if dados.nome:
        categoria.nome = dados.nome
    if dados.prazo_sla_horas:
        categoria.prazo_sla = timedelta(hours=dados.prazo_sla_horas)
    if dados.ativo is not None:
        categoria.excluido_logicamente = not dados.ativo
        
    db.commit()
    db.refresh(categoria)
    return categoria