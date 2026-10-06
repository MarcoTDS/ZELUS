from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from models.vinculo import VinculoMoradorDB, StatusVinculoEnum
from models.condominio import CondominioDB, UnidadeDB
from models.usuario import UsuarioDB
from models.enums import TipoUnidadeEnum
from schemas.vinculo import VinculoCreate

# ==========================================
# CONSULTAS DE APOIO (usadas por outros services)
# ==========================================
def obter_responsavel_unidade(db: Session, id_unidade: int, ignorar_id_usuario: int = None):
    # RN11/RN17: Morador ativo com vínculo aprovado na unidade
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
    # Situação do morador: "Aprovado" se tiver alguma unidade aprovada; senão "Pendente" ou "Rejeitado"
    status = {v.status_aprovacao for v in db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.ativo == True
    ).all()}

    for possivel in (StatusVinculoEnum.Aprovado, StatusVinculoEnum.Pendente, StatusVinculoEnum.Rejeitado):
        if possivel in status:
            return possivel.value
    return None

def obter_id_condominio_do_morador(db: Session, id_usuario: int):
    # Prioriza o condomínio de um vínculo aprovado; senão, o da solicitação pendente
    vinculos = db.query(VinculoMoradorDB).join(UnidadeDB).filter(
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.ativo == True,
        VinculoMoradorDB.status_aprovacao != StatusVinculoEnum.Rejeitado
    ).all()

    vinculos.sort(key=lambda v: v.status_aprovacao != StatusVinculoEnum.Aprovado)
    return vinculos[0].unidade.id_condominio if vinculos else None

def listar_unidades_do_morador(db: Session, id_usuario: int):
    # Unidades com vínculo aprovado (onde o morador pode abrir chamados - RN05)
    return db.query(UnidadeDB).join(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.status_aprovacao == StatusVinculoEnum.Aprovado,
        VinculoMoradorDB.ativo == True,
        UnidadeDB.ativo == True
    ).all()

def morador_pertence_ao_condominio(db: Session, id_usuario: int, id_condominio: int) -> bool:
    return db.query(VinculoMoradorDB).join(UnidadeDB).filter(
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.ativo == True,
        UnidadeDB.id_condominio == id_condominio
    ).first() is not None

# ==========================================
# SOLICITAÇÃO E AVALIAÇÃO DE VÍNCULOS
# ==========================================
def criar_solicitacao(db: Session, id_usuario: int, id_unidade: int):
    # Não faz commit: usado também no cadastro do morador (usuário + vínculo na mesma transação)
    unidade = db.query(UnidadeDB).join(CondominioDB).filter(
        UnidadeDB.id == id_unidade,
        UnidadeDB.ativo == True,
        CondominioDB.ativo == True
    ).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")

    if unidade.tipo_unidade == TipoUnidadeEnum.Area_Comum:
        raise HTTPException(status_code=400, detail="Não é possível solicitar vínculo com uma área comum.")

    # O banco permite apenas um vínculo ativo por morador/unidade (índice uq_usuario_unidade_ativo)
    vinculo_existente = db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_usuario == id_usuario,
        VinculoMoradorDB.id_unidade == id_unidade,
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
        id_unidade=id_unidade
    )
    db.add(novo_vinculo)
    db.flush()
    return novo_vinculo

def solicitar_vinculo(db: Session, id_usuario: int, dados: VinculoCreate):
    # RF06: Morador já cadastrado solicita vínculo com (outra) unidade
    novo_vinculo = criar_solicitacao(db, id_usuario, dados.id_unidade)
    db.commit()
    db.refresh(novo_vinculo)
    return novo_vinculo

def listar_pendentes(db: Session, id_condominio: int):
    # RF11: Vínculos pendentes das unidades do condomínio do síndico
    pendentes = db.query(VinculoMoradorDB).join(UnidadeDB).join(UsuarioDB, VinculoMoradorDB.id_usuario == UsuarioDB.id).filter(
        VinculoMoradorDB.status_aprovacao == StatusVinculoEnum.Pendente,
        VinculoMoradorDB.ativo == True,
        UnidadeDB.id_condominio == id_condominio,
        UnidadeDB.ativo == True,
        UsuarioDB.ativo == True
    ).order_by(VinculoMoradorDB.data_solicitacao).all()

    # RN11: Aviso quando a unidade já possui um morador responsável (atributo dinâmico, não persistido)
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
        
    # RN11: O síndico pode "aprovar mesmo assim" quando a unidade já possui responsável
    vinculo.status_aprovacao = StatusVinculoEnum.Aprovado if aprovado else StatusVinculoEnum.Rejeitado
    vinculo.data_avaliacao = datetime.utcnow()
    
    db.commit()
    db.refresh(vinculo)
    return vinculo

# ==========================================
# GERENCIAMENTO DE MORADORES (RF21)
# ==========================================
def listar_moradores(db: Session, id_condominio: int):
    # Vínculos aprovados do condomínio, incluindo moradores inativados (exibidos como "Inativo")
    return db.query(VinculoMoradorDB).join(UnidadeDB).join(UsuarioDB, VinculoMoradorDB.id_usuario == UsuarioDB.id).filter(
        VinculoMoradorDB.status_aprovacao == StatusVinculoEnum.Aprovado,
        VinculoMoradorDB.ativo == True,
        UnidadeDB.id_condominio == id_condominio
    ).order_by(UsuarioDB.nome).all()
