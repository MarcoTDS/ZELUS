from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from models.vinculo import VinculoMoradorDB, StatusVinculoEnum
from models.condominio import CondominioDB, UnidadeDB
from models.usuario import UsuarioDB
from models.enums import TipoUnidadeEnum, PerfilUsuarioEnum
from schemas.vinculo import VinculoCreate


def obter_responsavel_unidade(db: Session, id_unidade: int, ignorar_id_usuario: int = None):
    query = db.query(UsuarioDB).join(VinculoMoradorDB, VinculoMoradorDB.id_usuario == UsuarioDB.id).filter(
        VinculoMoradorDB.id_unidade == id_unidade,
        VinculoMoradorDB.status_aprovacao == StatusVinculoEnum.Aprovado,
        VinculoMoradorDB.ativo == True,
        UsuarioDB.ativo == True
    )
    if ignorar_id_usuario is not None:
        query = query.filter(UsuarioDB.id != ignorar_id_usuario)
    return query.first()

def obter_status_vinculo(db: Session, id_usuario: int):
    status = {v.status_aprovacao for v in db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.ativo == True
    ).all()}

    for possivel in (StatusVinculoEnum.Aprovado, StatusVinculoEnum.Pendente, StatusVinculoEnum.Rejeitado):
        if possivel in status:
            return possivel.value
    return None

def obter_id_condominio_do_morador(db: Session, id_usuario: int):
    vinculos = db.query(VinculoMoradorDB).join(UnidadeDB).filter(
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.ativo == True,
        VinculoMoradorDB.status_aprovacao != StatusVinculoEnum.Rejeitado
    ).all()

    vinculos.sort(key=lambda v: v.status_aprovacao != StatusVinculoEnum.Aprovado)
    return vinculos[0].unidade.id_condominio if vinculos else None

def listar_unidades_do_morador(db: Session, id_usuario: int):
    return db.query(UnidadeDB).join(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.status_aprovacao == StatusVinculoEnum.Aprovado,
        VinculoMoradorDB.ativo == True,
        UnidadeDB.ativo == True
    ).all()

def morador_sem_unidade(db: Session, usuario: UsuarioDB) -> bool:
    if usuario.perfil != PerfilUsuarioEnum.Morador:
        return False
    return db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_usuario == usuario.id,
        VinculoMoradorDB.status_aprovacao != StatusVinculoEnum.Rejeitado,
        VinculoMoradorDB.ativo == True
    ).first() is None

def morador_pertence_ao_condominio(db: Session, id_usuario: int, id_condominio: int) -> bool:
    return db.query(VinculoMoradorDB).join(UnidadeDB).join(UsuarioDB, VinculoMoradorDB.id_usuario == UsuarioDB.id).filter(
        UsuarioDB.perfil == PerfilUsuarioEnum.Morador,
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.ativo == True,
        UnidadeDB.id_condominio == id_condominio
    ).first() is not None

def criar_solicitacao(db: Session, id_usuario: int, id_unidade: int):
    unidade = db.query(UnidadeDB).join(CondominioDB).filter(
        UnidadeDB.id == id_unidade,
        UnidadeDB.ativo == True,
        CondominioDB.ativo == True
    ).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")

    if unidade.tipo_unidade == TipoUnidadeEnum.Area_Comum:
        raise HTTPException(status_code=400, detail="Não é possível solicitar vínculo com uma área comum.")

    id_condominio_atual = obter_id_condominio_do_morador(db, id_usuario)
    if id_condominio_atual is not None and id_condominio_atual != unidade.id_condominio:
        raise HTTPException(status_code=400, detail="Todas as unidades devem ser do mesmo condomínio.")

    vinculo_existente = db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.id_unidade == id_unidade,
        VinculoMoradorDB.ativo == True
    ).first()

    if vinculo_existente:
        if vinculo_existente.status_aprovacao != StatusVinculoEnum.Rejeitado:
            raise HTTPException(status_code=409, detail="Já existe uma solicitação pendente ou aprovada para esta unidade.")
        vinculo_existente.ativo = False
        db.flush()

    novo_vinculo = VinculoMoradorDB(
        id_usuario=id_usuario,
        id_unidade=id_unidade
    )
    db.add(novo_vinculo)
    db.flush()
    return novo_vinculo

def solicitar_vinculo(db: Session, id_usuario: int, dados: VinculoCreate):
    novo_vinculo = criar_solicitacao(db, id_usuario, dados.id_unidade)
    db.commit()
    db.refresh(novo_vinculo)
    return novo_vinculo

def listar_vinculos_do_morador(db: Session, id_usuario: int):
    return db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.ativo == True
    ).order_by(VinculoMoradorDB.data_solicitacao).all()

def encerrar_vinculo_do_morador(db: Session, id_vinculo: int, id_usuario: int):
    vinculo = db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id == id_vinculo,
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.ativo == True
    ).first()
    if not vinculo:
        return None

    if vinculo.status_aprovacao == StatusVinculoEnum.Aprovado and len(listar_unidades_do_morador(db, id_usuario)) <= 1:
        raise HTTPException(status_code=400, detail="Esta é a sua única unidade aprovada. Para deixar o condomínio, procure o síndico.")

    vinculo.ativo = False
    db.commit()
    db.refresh(vinculo)
    return vinculo

def listar_pendentes(db: Session, id_condominio: int):
    pendentes = db.query(VinculoMoradorDB).join(UnidadeDB).join(UsuarioDB, VinculoMoradorDB.id_usuario == UsuarioDB.id).filter(
        VinculoMoradorDB.status_aprovacao == StatusVinculoEnum.Pendente,
        VinculoMoradorDB.ativo == True,
        UnidadeDB.id_condominio == id_condominio,
        UnidadeDB.ativo == True,
        UsuarioDB.ativo == True,
        UsuarioDB.perfil == PerfilUsuarioEnum.Morador # o síndico não aprova o próprio pedido
    ).order_by(VinculoMoradorDB.data_solicitacao).all()

    for vinculo in pendentes:
        responsavel = obter_responsavel_unidade(db, vinculo.id_unidade, ignorar_id_usuario=vinculo.id_usuario)
        vinculo.responsavel_atual = responsavel.nome if responsavel else None

    return pendentes

def avaliar_vinculo(db: Session, id_vinculo: int, id_condominio: int, aprovado: bool):
    vinculo = db.query(VinculoMoradorDB).join(UnidadeDB).filter(
        VinculoMoradorDB.id == id_vinculo,
        VinculoMoradorDB.ativo == True,
        UnidadeDB.id_condominio == id_condominio # RN14: apenas vínculos do condomínio do síndico
    ).first()
    if not vinculo:
        return None

    if vinculo.status_aprovacao != StatusVinculoEnum.Pendente:
        raise HTTPException(status_code=400, detail="Este vínculo já foi avaliado.")
        
    vinculo.status_aprovacao = StatusVinculoEnum.Aprovado if aprovado else StatusVinculoEnum.Rejeitado
    vinculo.data_avaliacao = datetime.utcnow()
    
    db.commit()
    db.refresh(vinculo)
    return vinculo

def listar_moradores(db: Session, id_condominio: int):
    return db.query(VinculoMoradorDB).join(UnidadeDB).join(UsuarioDB, VinculoMoradorDB.id_usuario == UsuarioDB.id).filter(
        UsuarioDB.perfil == PerfilUsuarioEnum.Morador,
        VinculoMoradorDB.status_aprovacao == StatusVinculoEnum.Aprovado,
        VinculoMoradorDB.ativo == True,
        UnidadeDB.id_condominio == id_condominio
    ).order_by(UsuarioDB.nome).all()

def remover_morador_da_unidade(db: Session, id_vinculo: int, id_condominio: int):
    vinculo = db.query(VinculoMoradorDB).join(UnidadeDB).join(UsuarioDB, VinculoMoradorDB.id_usuario == UsuarioDB.id).filter(
        UsuarioDB.perfil == PerfilUsuarioEnum.Morador, 
        VinculoMoradorDB.id == id_vinculo,
        VinculoMoradorDB.status_aprovacao == StatusVinculoEnum.Aprovado,
        VinculoMoradorDB.ativo == True,
        UnidadeDB.id_condominio == id_condominio # RN14
    ).first()
    if not vinculo:
        return None

    vinculo.ativo = False
    db.flush()

    outras_unidades = db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_usuario == vinculo.id_usuario,
        VinculoMoradorDB.status_aprovacao != StatusVinculoEnum.Rejeitado,
        VinculoMoradorDB.ativo == True
    ).count()
    usuario_inativado = outras_unidades == 0
    if usuario_inativado:
        vinculo.usuario.ativo = False

    db.commit()
    return {"id": vinculo.id, "usuario_inativado": usuario_inativado}
