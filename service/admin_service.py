from sqlalchemy.orm import Session
import uuid
import string
import random

from models.condominio import CondominioDB, UnidadeDB, SindicoCondominioDB
from models.usuario import UsuarioDB
from models.enums import PerfilUsuarioEnum
from schemas.admin import CondominioCreate, SindicoCreate
from service.usuario_service import obter_hash_senha

def cadastrar_condominio_lote(db: Session, dados: CondominioCreate):
    # Cadastra o condomínio
    novo_condominio = CondominioDB(
        nome=dados.nome,
        endereco=dados.endereco
    )
    db.add(novo_condominio)
    db.flush() # Gera o ID do condomínio sem comitar a transação

    # Prepara as unidades para inserção em lote (Bulk Insert)
    unidades_db = [
        UnidadeDB(
            id_condominio=novo_condominio.id,
            bloco=unidade.bloco,
            numero=unidade.numero
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
    # RN13: Gera senha provisória aleatória
    senha_plana = gerar_senha_aleatoria()
    
    # RN12: Gera token de validação para o primeiro acesso
    token_validacao = str(uuid.uuid4())
    
    novo_usuario = UsuarioDB(
        email=dados.email,
        senha_hash=obter_hash_senha(senha_plana),
        perfil=PerfilUsuarioEnum.Sindico,
        senha_provisoria=True,
        token_validacao=token_validacao
    )
    db.add(novo_usuario)
    db.flush()

    # RN07: Vincula o síndico ao condomínio
    vinculo = SindicoCondominioDB(
        id_usuario_sindico=novo_usuario.id,
        id_condominio=dados.id_condominio
    )
    db.add(vinculo)
    db.commit()
    
    # Para fins de demonstração (já que não temos envio real de e-mail configurado), 
    # retornamos a senha provisória no response.
    return {
        "id_usuario": novo_usuario.id,
        "email": novo_usuario.email,
        "senha_provisoria": senha_plana,
        "link_validacao": f"http://127.0.0.1:8000/auth/validar?token={token_validacao}"
    }