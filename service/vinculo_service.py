from sqlalchemy.orm import Session
from datetime import datetime
from models.vinculo import VinculoMoradorDB, StatusVinculoEnum
from schemas.vinculo import VinculoCreate

def solicitar_vinculo(db: Session, id_usuario: int, dados: VinculoCreate):
    novo_vinculo = VinculoMoradorDB(
        id_usuario=id_usuario,
        id_unidade=dados.id_unidade
    )
    db.add(novo_vinculo)
    db.commit()
    db.refresh(novo_vinculo)
    return novo_vinculo

def listar_pendentes(db: Session, id_condominio: int):
    # Retorna vínculos pendentes com base nas unidades do condomínio do síndico
    from models.condominio import UnidadeDB
    return db.query(VinculoMoradorDB).join(UnidadeDB).filter(
        VinculoMoradorDB.status == StatusVinculoEnum.Pendente,
        UnidadeDB.id_condominio == id_condominio
    ).all()

def avaliar_vinculo(db: Session, id_vinculo: int, id_avaliador: int, aprovado: bool):
    vinculo = db.query(VinculoMoradorDB).filter(VinculoMoradorDB.id == id_vinculo).first()
    if not vinculo:
        return None
        
    vinculo.status = StatusVinculoEnum.Aprovado if aprovado else StatusVinculoEnum.Rejeitado
    vinculo.id_avaliador = id_avaliador
    vinculo.data_avaliacao = datetime.utcnow()
    
    db.commit()
    db.refresh(vinculo)
    return vinculo