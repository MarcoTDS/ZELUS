from sqlalchemy.orm import Session
from fastapi import HTTPException
import string
import random

from models.condominio import CondominioDB, UnidadeDB
from models.categoria import CategoriaDB
from models.chamado import ChamadoDB
from models.vinculo import VinculoMoradorDB
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

    # RN15: Indica se o condomínio pode ser inativado (a lixeira fica desabilitada na tela)
    for condominio in condominios:
        condominio.pode_inativar = condominio.ativo and _motivo_bloqueio_inativacao(db, condominio) is None

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
    # RN15: Só pode ser inativado sem vínculos existentes (síndico, moradores, unidades com chamados)
    if condominio.id_sindico is not None:
        return "o condomínio possui um síndico vinculado"

    ids_unidades = [u.id for u in condominio.unidades]
    if not ids_unidades:
        return None

    if db.query(VinculoMoradorDB).filter(
        VinculoMoradorDB.id_unidade.in_(ids_unidades),
        VinculoMoradorDB.ativo == True
    ).first():
        return "o condomínio possui moradores vinculados"

    if db.query(ChamadoDB).filter(ChamadoDB.id_unidade_destino.in_(ids_unidades)).first():
        return "o condomínio possui unidades com chamados"

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
    for unidade in condominio.unidades:
        unidade.ativo = False
    db.query(CategoriaDB).filter(CategoriaDB.id_condominio == condominio.id).update({CategoriaDB.ativo: False})

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

def cadastrar_sindico(db: Session, dados: SindicoCreate):
    condominio = buscar_condominio(db, dados.id_condominio)
    if not condominio:
        raise HTTPException(status_code=404, detail="Condomínio não encontrado.")

    # RN07: Cada condomínio possui exatamente um síndico responsável
    if condominio.id_sindico is not None:
        raise HTTPException(status_code=409, detail="Este condomínio já possui um síndico responsável.")

    if obter_usuario_por_email(db, dados.email):
        raise HTTPException(status_code=409, detail="Já existe um usuário cadastrado com este e-mail.")

    novo_sindico = UsuarioDB(
        nome=dados.nome,
        email=dados.email,
        senha="", # Definida em _enviar_acesso_sindico
        perfil=PerfilUsuarioEnum.Sindico,
        email_validado=False # RN12
    )
    db.add(novo_sindico)
    db.flush()

    condominio.id_sindico = novo_sindico.id

    resultado = _enviar_acesso_sindico(db, novo_sindico, condominio.nome)
    resultado["id_condominio"] = condominio.id
    return resultado

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
