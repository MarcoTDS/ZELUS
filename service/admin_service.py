from sqlalchemy.orm import Session
from fastapi import HTTPException
import string
from datetime import datetime
import random

from models.condominio import CondominioDB, UnidadeDB
from models.categoria import CategoriaDB
from models.chamado import ChamadoDB
from models.vinculo import VinculoMoradorDB, StatusVinculoEnum
from models.enums import StatusChamadoEnum
from models.usuario import UsuarioDB
from models.enums import PerfilUsuarioEnum, TipoTokenEnum
from schemas.admin import CondominioCreate, CondominioUpdate, SindicoCreate
from service import token_service, unidade_service
from service.usuario_service import obter_hash_senha, obter_usuario_por_email, URL_FRONTEND
from service.email_service import enviar_email

CAMPOS_ENDERECO = ["nome", "cep", "numero", "rua", "bairro", "cidade", "estado"]

# ==========================================
# CONDOMÍNIOS (RF04, RF12, RN15)
# ==========================================
def buscar_condominio(db: Session, id_condominio: int):
    return db.query(CondominioDB).filter(
        CondominioDB.id == id_condominio,
        CondominioDB.ativo == True
    ).first()

def listar_condominios(db: Session, incluir_inativos: bool = False):
    # RF04: Dashboard do Administrador (nome do síndico via relationship CondominioDB.sindico)
    query = db.query(CondominioDB)
    if not incluir_inativos:
        query = query.filter(CondominioDB.ativo == True)
    condominios = query.order_by(CondominioDB.nome).all()

    # RN15: Indica se o condomínio pode ser inativado (a lixeira fica desabilitada na tela, com o motivo)
    for condominio in condominios:
        condominio.motivo_bloqueio = _motivo_bloqueio_inativacao(db, condominio) if condominio.ativo else None
        condominio.pode_inativar = condominio.ativo and condominio.motivo_bloqueio is None

    return condominios

def cadastrar_condominio_lote(db: Session, dados: CondominioCreate):
    # Valida todas as unidades antes de gravar qualquer coisa
    unidades_db = [unidade_service.montar_unidade(None, unidade) for unidade in dados.unidades]

    identificacoes = [u.identificacao.lower() for u in unidades_db]
    if len(identificacoes) != len(set(identificacoes)):
        raise HTTPException(status_code=400, detail="A lista possui unidades repetidas.")

    # Cadastra o condomínio (o síndico é vinculado depois, no cadastro do síndico - RF13)
    novo_condominio = CondominioDB(**{campo: getattr(dados, campo) for campo in CAMPOS_ENDERECO})
    novo_condominio.estado = novo_condominio.estado.upper()
    db.add(novo_condominio)
    db.flush() # Gera o ID do condomínio sem comitar a transação

    # Inserção em lote (Bulk Insert) das unidades
    for unidade in unidades_db:
        unidade.id_condominio = novo_condominio.id
    db.add_all(unidades_db)

    db.commit()
    db.refresh(novo_condominio)
    return novo_condominio

def editar_condominio(db: Session, id_condominio: int, dados: CondominioUpdate):
    # RN15: A edição do condomínio é permitida a qualquer momento
    condominio = buscar_condominio(db, id_condominio)
    if not condominio:
        return None

    for campo in CAMPOS_ENDERECO:
        valor = getattr(dados, campo)
        if valor is not None:
            setattr(condominio, campo, valor.upper() if campo == "estado" else valor)

    db.commit()
    db.refresh(condominio)
    return condominio

def _motivo_bloqueio_inativacao(db: Session, condominio: CondominioDB):
    # RN15: Só pode ser inativado sem vínculos ativos (síndico, moradores aprovados, chamados em aberto)
    if condominio.id_sindico is not None:
        return "o condomínio possui um síndico vinculado"

    ids_unidades = [u.id for u in condominio.unidades]
    if not ids_unidades:
        return None

    if db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_unidade.in_(ids_unidades),
        VinculoMoradorDB.status_aprovacao == StatusVinculoEnum.Aprovado,
        VinculoMoradorDB.ativo == True
    ).first():
        return "o condomínio possui moradores vinculados"

    # Chamados resolvidos ou cancelados não bloqueiam: continuam guardados como histórico (RN08)
    if db.query(ChamadoDB).filter(
        ChamadoDB.id_unidade_destino.in_(ids_unidades),
        ChamadoDB.status.in_([StatusChamadoEnum.Aberto, StatusChamadoEnum.Em_Andamento])
    ).first():
        return "o condomínio possui chamados em aberto"

    return None

def inativar_condominio(db: Session, id_condominio: int):
    condominio = buscar_condominio(db, id_condominio)
    if not condominio:
        return None

    motivo = _motivo_bloqueio_inativacao(db, condominio)
    if motivo:
        raise HTTPException(status_code=400, detail=f"Não é possível inativar: {motivo}.")

    # Soft Delete (RN08) do condomínio e dos seus dependentes
    condominio.ativo = False

    # Solicitações de cadastro ainda pendentes são rejeitadas (a unidade deixa de existir)
    ids_unidades = [u.id for u in condominio.unidades]
    if ids_unidades:
        db.query(VinculoMoradorDB).filter(
            VinculoMoradorDB.id_unidade.in_(ids_unidades),
            VinculoMoradorDB.status_aprovacao == StatusVinculoEnum.Pendente,
            VinculoMoradorDB.ativo == True
        ).update({
            VinculoMoradorDB.status_aprovacao: StatusVinculoEnum.Rejeitado,
            VinculoMoradorDB.data_avaliacao: datetime.utcnow()
        }, synchronize_session=False)

    for unidade in condominio.unidades:
        unidade.ativo = False
    db.query(CategoriaDB).filter(CategoriaDB.id_condominio == condominio.id).update({CategoriaDB.ativo: False})

    db.commit()
    db.refresh(condominio)
    return condominio

def reativar_condominio(db: Session, id_condominio: int):
    # Desfaz a inativação: o condomínio, as unidades e as categorias dele voltam a ficar ativos.
    # Só é possível chegar aqui com o condomínio sem síndico nem moradores (RN15), então ele volta
    # sem síndico até o administrador cadastrar um (RF13). Solicitações rejeitadas na inativação continuam rejeitadas.
    condominio = db.query(CondominioDB).filter(CondominioDB.id == id_condominio).first()
    if not condominio:
        return None

    if condominio.ativo:
        raise HTTPException(status_code=400, detail="Este condomínio já está ativo.")

    condominio.ativo = True
    db.query(UnidadeDB).filter(UnidadeDB.id_condominio == condominio.id).update({UnidadeDB.ativo: True})
    db.query(CategoriaDB).filter(CategoriaDB.id_condominio == condominio.id).update({CategoriaDB.ativo: True})

    db.commit()
    db.refresh(condominio)
    return condominio

# ==========================================
# SÍNDICOS (RF13, RN07, RN12, RN13)
# ==========================================
def gerar_senha_aleatoria(tamanho=10):
    caracteres = string.ascii_letters + string.digits + "@#$"
    return ''.join(random.SystemRandom().choice(caracteres) for i in range(tamanho))

def _enviar_acesso_sindico(db: Session, sindico: UsuarioDB, condominio_nome: str):
    # RN13: Nova senha provisória (só o hash fica no banco, então ela é gerada novamente a cada envio)
    senha_plana = gerar_senha_aleatoria()
    sindico.senha = obter_hash_senha(senha_plana)
    sindico.senha_provisoria = True

    # RN12: Link de validação do e-mail (invalida links anteriores)
    token = token_service.gerar_token(db, sindico.id, TipoTokenEnum.Validacao_Email)
    link_validacao = f"{URL_FRONTEND}/views/auth/validar-email.html?token={token}"
    db.commit()

    email_enviado = enviar_email(
        sindico.email,
        "Zelus - Seu acesso como síndico",
        f"Olá, {sindico.nome}!\n\nVocê foi cadastrado como síndico do condomínio {condominio_nome}.\n"
        f"1) Valide seu e-mail (link válido por 2 dias): {link_validacao}\n"
        f"2) Acesse o sistema com a senha provisória: {senha_plana}\n"
        f"No primeiro acesso será obrigatório definir uma nova senha."
    )

    # Os dados de acesso também voltam no response: se o e-mail falhar, o administrador consegue repassá-los
    return {
        "id_usuario": sindico.id,
        "nome": sindico.nome,
        "email": sindico.email,
        "senha_provisoria": senha_plana,
        "link_validacao": link_validacao,
        "email_enviado": email_enviado
    }

def _reaproveitar_ex_sindico(db: Session, usuario: UsuarioDB, nome: str):
    # Um ex-síndico (desvinculado e sem condomínio) pode assumir outro condomínio com a mesma conta.
    # Cada usuário tem um único perfil: um morador que vira síndico recebe uma conta de síndico com outro e-mail.
    if usuario.perfil == PerfilUsuarioEnum.Morador:
        raise HTTPException(status_code=409, detail="Este e-mail pertence a uma conta de morador. Para o morador assumir como síndico, cadastre-o com outro e-mail (a conta de morador continua valendo para abrir chamados).")
    if usuario.perfil != PerfilUsuarioEnum.Sindico:
        raise HTTPException(status_code=409, detail="Já existe um usuário cadastrado com este e-mail.")

    # RN07: cada síndico gerencia exatamente um condomínio
    if db.query(CondominioDB).filter(CondominioDB.id_sindico == usuario.id, CondominioDB.ativo == True).first():
        raise HTTPException(status_code=409, detail="Este síndico já é responsável por outro condomínio.")

    # Volta a ter acesso, com nova senha provisória e novo link de validação (RN12, RN13)
    usuario.nome = nome
    usuario.ativo = True
    usuario.email_validado = False
    return usuario

def cadastrar_sindico(db: Session, dados: SindicoCreate):
    condominio = buscar_condominio(db, dados.id_condominio)
    if not condominio:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")

    # RN07: Cada condomínio possui exatamente um síndico responsável
    if condominio.id_sindico is not None:
        raise HTTPException(status_code=409, detail="Este condomínio já possui um síndico responsável.")

    existente = obter_usuario_por_email(db, dados.email)
    if existente:
        sindico = _reaproveitar_ex_sindico(db, existente, dados.nome)
    else:
        sindico = UsuarioDB(
            nome=dados.nome,
            email=dados.email,
            senha="", # Definida em _enviar_acesso_sindico
            perfil=PerfilUsuarioEnum.Sindico,
            email_validado=False # RN12
        )
        db.add(sindico)
        db.flush()

    condominio.id_sindico = sindico.id

    resultado = _enviar_acesso_sindico(db, sindico, condominio.nome)
    resultado["id_condominio"] = condominio.id
    return resultado

def desvincular_sindico(db: Session, id_condominio: int):
    # RN07, RN15: Tira o síndico do condomínio (troca de síndico ou encerramento do condomínio).
    # Como cada síndico gerencia exatamente um condomínio, o usuário dele é inativado (RN08).
    condominio = buscar_condominio(db, id_condominio)
    if not condominio:
        return None

    if condominio.id_sindico is None:
        raise HTTPException(status_code=400, detail="Este condomínio não possui síndico vinculado.")

    sindico = db.query(UsuarioDB).filter(UsuarioDB.id == condominio.id_sindico).first()
    condominio.id_sindico = None
    if sindico:
        sindico.ativo = False

    db.commit()
    db.refresh(condominio)
    return condominio

def sindico_sair_do_condominio(db: Session, id_condominio: int):
    # RN18: O próprio síndico pode deixar o condomínio, desde que não haja chamados Aberto ou Em Andamento.
    # O condomínio fica sem síndico até o administrador cadastrar outro (RF13).
    em_aberto = db.query(ChamadoDB).join(UnidadeDB, ChamadoDB.id_unidade_destino == UnidadeDB.id).filter(
        UnidadeDB.id_condominio == id_condominio,
        ChamadoDB.status.in_([StatusChamadoEnum.Aberto, StatusChamadoEnum.Em_Andamento])
    ).count()
    if em_aberto:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível sair do condomínio: há {em_aberto} chamado(s) Aberto ou Em Andamento. Resolva ou cancele antes."
        )
    return desvincular_sindico(db, id_condominio)

def reenviar_link_validacao(db: Session, id_usuario: int):
    sindico = db.query(UsuarioDB).filter(
        UsuarioDB.id == id_usuario,
        UsuarioDB.perfil == PerfilUsuarioEnum.Sindico,
        UsuarioDB.ativo == True
    ).first()
    if not sindico:
        raise HTTPException(status_code=404, detail="Síndico não encontrado.")

    if sindico.email_validado:
        raise HTTPException(status_code=400, detail="O e-mail deste síndico já foi validado.")

    condominio = db.query(CondominioDB).filter(CondominioDB.id_sindico == sindico.id).first()

    resultado = _enviar_acesso_sindico(db, sindico, condominio.nome if condominio else "-")
    resultado["id_condominio"] = condominio.id if condominio else None
    return resultado