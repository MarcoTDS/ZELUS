from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.vinculo import VinculoMoradorDB, StatusVinculoEnum
from models.condominio import CondominioDB, UnidadeDB
from schemas.vinculo import VinculoCreate

def solicitar_vinculo(db: Session, id_usuario: int, dados: VinculoCreate):
    unidade = db.query(UnidadeDB).filter(
        UnidadeDB.id == dados.id_unidade,
        UnidadeDB.ativo == True
    ).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")

    # O banco permite apenas um vínculo ativo por morador/unidade (índice uq_usuario_unidade_ativo)
    vinculo_existente = db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.id_unidade == dados.id_unidade,
        VinculoMoradorDB.ativo == True
    ).first()

    if vinculo_existente:
        if vinculo_existente.status_aprovacao != StatusVinculoEnum.Rejeitado:
            raise HTTPException(status_code=409, detail="Já existe uma solicitação pendente ou aprovada para esta unidade.")
        # Uma solicitação rejeitada é inativada para permitir um novo pedido
        vinculo_existente.ativo = False
        db.flush()

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
    return db.query(VinculoMoradorDB).join(UnidadeDB).filter(
        VinculoMoradorDB.status_aprovacao == StatusVinculoEnum.Pendente,
        VinculoMoradorDB.ativo == True,
        UnidadeDB.id_condominio == id_condominio,
        UnidadeDB.ativo == True
    ).all()

def avaliar_vinculo(db: Session, id_vinculo: int, id_avaliador: int, aprovado: bool):
    vinculo = db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id == id_vinculo,
        VinculoMoradorDB.ativo == True
    ).first()
    if not vinculo:
        return None

    # Apenas o síndico responsável pelo condomínio da unidade pode avaliar
    condominio = db.query(CondominioDB).join(UnidadeDB).filter(
        UnidadeDB.id == vinculo.id_unidade
    ).first()
    if not condominio or condominio.id_sindico != id_avaliador:
        raise HTTPException(status_code=403, detail="Apenas o síndico do condomínio pode avaliar este vínculo.")

    if vinculo.status_aprovacao != StatusVinculoEnum.Pendente:
        raise HTTPException(status_code=400, detail="Este vínculo já foi avaliado.")
        
    vinculo.status_aprovacao = StatusVinculoEnum.Aprovado if aprovado else StatusVinculoEnum.Rejeitado
    
    db.commit()
    db.refresh(vinculo)
    return vinculo