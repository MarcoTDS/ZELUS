from sqlalchemy.orm import Session
from fastapi import HTTPException
import string
import random

from models.condominio import CondominioDB, UnidadeDB
from models.usuario import UsuarioDB
from models.enums import PerfilUsuarioEnum, TipoCondominioEnum
from schemas.admin import CondominioCreate, SindicoCreate
from service.usuario_service import obter_hash_senha, obter_usuario_por_email

def _validar_unidade(tipo_condominio: TipoCondominioEnum, unidade):
    # Espelha a CHECK constraint "ck_unidade_identificacao" do banco
    if tipo_condominio == TipoCondominioEnum.Apartamento and not unidade.apartamento:
        raise HTTPException(status_code=400, detail="Unidades do tipo Apartamento exigem o número do apartamento.")
    if tipo_condominio == TipoCondominioEnum.Casa and not unidade.numero_casa:
        raise HTTPException(status_code=400, detail="Unidades do tipo Casa exigem o número da casa.")

def cadastrar_condominio_lote(db: Session, dados: CondominioCreate):
    # RN07: O condomínio precisa de um síndico responsável (id_sindico é NOT NULL)
    sindico = db.query(UsuarioDB).filter(
        UsuarioDB.id == dados.id_sindico,
        UsuarioDB.ativo == True
    ).first()

    if not sindico or sindico.perfil != PerfilUsuarioEnum.Sindico:
        raise HTTPException(status_code=400, detail="O id_sindico informado não pertence a um síndico ativo.")

    for unidade in dados.unidades:
        _validar_unidade(dados.tipo_condominio, unidade)

    # Cadastra o condomínio
    novo_condominio = CondominioDB(
        nome=dados.nome,
        cep=dados.cep,
        numero=dados.numero,
        rua=dados.rua,
        bairro=dados.bairro,
        cidade=dados.cidade,
        estado=dados.estado.upper(),
        id_sindico=dados.id_sindico
    )
    db.add(novo_condominio)
    db.flush() # Gera o ID do condomínio sem comitar a transação

    # Prepara as unidades para inserção em lote (Bulk Insert)
    unidades_db = [
        UnidadeDB(
            id_condominio=novo_condominio.id,
            tipo_condominio=dados.tipo_condominio,
            bloco=unidade.bloco,
            apartamento=unidade.apartamento,
            rua=unidade.rua,
            numero_casa=unidade.numero_casa
        )
        for unidade in dados.unidades
    ]
    
    db.add_all(unidades_db)
    db.commit()
    db.refresh(novo_condominio)
    
    return novo_condominio

def gerar_senha_aleatoria(tamanho=8):
    caracteres = string.ascii_letters + string.digits + "@#$"
    return ''.join(random.choice(caracteres) for i in range(tamanho))

def cadastrar_sindico(db: Session, dados: SindicoCreate):
    if obter_usuario_por_email(db, dados.email):
        raise HTTPException(status_code=409, detail="Já existe um usuário cadastrado com este e-mail.")

    # RN07: Se informado, o condomínio passa a ter este síndico como responsável
    condominio = None
    if dados.id_condominio is not None:
        condominio = db.query(CondominioDB).filter(
            CondominioDB.id == dados.id_condominio,
            CondominioDB.ativo == True
        ).first()
        if not condominio:
            raise HTTPException(status_code=404, detail="Condomínio não encontrado.")

    # RN13: Gera senha provisória aleatória
    senha_plana = gerar_senha_aleatoria()
    
    novo_usuario = UsuarioDB(
        nome=dados.nome,
        email=dados.email,
        senha=obter_hash_senha(senha_plana),
        perfil=PerfilUsuarioEnum.Sindico
    )
    db.add(novo_usuario)
    db.flush()

    if condominio:
        condominio.id_sindico = novo_usuario.id

    db.commit()
    
    # Para fins de demonstração (já que não temos envio real de e-mail configurado), 
    # retornamos a senha provisória no response.
    return {
        "id_usuario": novo_usuario.id,
        "nome": novo_usuario.nome,
        "email": novo_usuario.email,
        "id_condominio": condominio.id if condominio else None,
        "senha_provisoria": senha_plana
    }