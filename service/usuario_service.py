import os
from sqlalchemy.orm import Session
from fastapi import HTTPException
import bcrypt
from datetime import datetime
from models.usuario import UsuarioDB
from models.enums import PerfilUsuarioEnum, TipoTokenEnum
from schemas.usuario import UsuarioCreate, CadastroMoradorRequest, SENHA_MIN
from service import token_service, vinculo_service
from service.email_service import enviar_email

URL_FRONTEND = os.getenv("ZELUS_URL_FRONTEND", "http://127.0.0.1:5501").rstrip("/")


def obter_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha_plana.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
    
        return False


def buscar_por_id(db: Session, id_usuario: int):
    return db.query(UsuarioDB).filter(
        UsuarioDB.id == id_usuario, 
        UsuarioDB.ativo == True
    ).first()

def buscar_por_email(db: Session, email: str):
    return db.query(UsuarioDB).filter(
        UsuarioDB.email == email, 
        UsuarioDB.ativo == True
    ).first()

def obter_usuario_por_email(db: Session, email: str):
    return db.query(UsuarioDB).filter(UsuarioDB.email == email).first()

def autenticar_usuario(db: Session, email: str, senha_plana: str):
    usuario = obter_usuario_por_email(db, email)
    if not usuario or not verificar_senha(senha_plana, usuario.senha):
        return None

    if not usuario.ativo:
        if vinculo_service.morador_sem_unidade(db, usuario):
            raise PermissionError("Sua conta não está vinculada a nenhuma unidade. Para solicitar uma nova, acesse \"Cadastre-se\" e informe este mesmo e-mail.")
        return None

    if not usuario.email_validado:
        raise PermissionError("E-mail ainda não validado. Acesse o link enviado para o seu e-mail.")

    usuario.ultimo_acesso = datetime.utcnow()
    db.commit()
    db.refresh(usuario)
        
    return usuario

def validar_email(db: Session, token: str):
    usuario = token_service.consumir_token(db, token, TipoTokenEnum.Validacao_Email)
    usuario.email_validado = True
    db.commit()
    db.refresh(usuario)
    return usuario

def criar_usuario(db: Session, usuario: UsuarioCreate):
    hash_senha = obter_hash_senha(usuario.senha)
    
    db_usuario = UsuarioDB(
        nome=usuario.nome,
        email=usuario.email,
        senha=hash_senha,
        perfil=usuario.perfil or PerfilUsuarioEnum.Morador
    )
    
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def verificar_email_cadastro(db: Session, email: str) -> str:
    usuario = obter_usuario_por_email(db, email)
    if not usuario:
        return "novo"        
    if vinculo_service.morador_sem_unidade(db, usuario):
        return "sem_unidade"   
    return "existente"        

def cadastrar_morador(db: Session, dados: CadastroMoradorRequest):
    usuario = obter_usuario_por_email(db, dados.email)

    if usuario:
        if not vinculo_service.morador_sem_unidade(db, usuario):
            raise ValueError("Já existe uma conta cadastrada com este e-mail.")
        if not verificar_senha(dados.senha, usuario.senha):
            raise HTTPException(status_code=401, detail="Senha incorreta. Informe a senha da sua conta.")
        usuario.ativo = True 
        novo_usuario = usuario
    else:
        if not dados.nome:
            raise HTTPException(status_code=400, detail="Informe o nome completo.")
        if len(dados.senha) < SENHA_MIN:
            raise HTTPException(status_code=400, detail=f"A senha deve ter pelo menos {SENHA_MIN} caracteres.")
        novo_usuario = UsuarioDB(
            nome=dados.nome,
            email=dados.email,
            senha=obter_hash_senha(dados.senha),
            perfil=PerfilUsuarioEnum.Morador
        )
        db.add(novo_usuario)
    db.flush()

    try:
        vinculos = [
            vinculo_service.criar_solicitacao(db, novo_usuario.id, id_unidade)
            for id_unidade in dict.fromkeys(dados.ids_unidades) # ignora unidades repetidas
        ]
    except Exception:
        db.rollback() 
        raise

    db.commit()
    db.refresh(novo_usuario)
    for vinculo in vinculos:
        db.refresh(vinculo)
    return novo_usuario, vinculos

def alterar_senha(db: Session, id_usuario: int, senha_atual: str, nova_senha: str):
    usuario = buscar_por_id(db, id_usuario)
    
    if not usuario:
        raise ValueError("Usuário não encontrado.")
        
    if not verificar_senha(senha_atual, usuario.senha):
        raise ValueError("A senha atual informada está incorreta.")

    if senha_atual == nova_senha:
        raise ValueError("A nova senha deve ser diferente da senha atual.")
        
    usuario.senha = obter_hash_senha(nova_senha)
    usuario.senha_provisoria = False 
    
    db.commit()
    db.refresh(usuario)
    return usuario

def solicitar_redefinicao_senha(db: Session, email: str):
    usuario = obter_usuario_por_email(db, email)
    if not usuario or not (usuario.ativo or vinculo_service.morador_sem_unidade(db, usuario)):
        return

    token = token_service.gerar_token(db, usuario.id, TipoTokenEnum.Redefinicao_Senha)
    db.commit()

    enviar_email(
        usuario.email,
        "Zelus - Redefinição de senha",
        f"Olá, {usuario.nome}!\n\nPara definir uma nova senha, acesse o link abaixo (válido por 1 hora):\n"
        f"{URL_FRONTEND}/views/auth/redefinir-senha.html?token={token}"
    )

def redefinir_senha(db: Session, token: str, nova_senha: str):
    usuario = token_service.consumir_token(db, token, TipoTokenEnum.Redefinicao_Senha)

    usuario.senha = obter_hash_senha(nova_senha)
    usuario.senha_provisoria = False
    usuario.email_validado = True 

    db.commit()
    db.refresh(usuario)
    return usuario

def atualizar_perfil(db: Session, id_usuario: int, nome: str = None, email: str = None):
    usuario = db.query(UsuarioDB).filter(UsuarioDB.id == id_usuario).first()
    
    if not usuario:
        raise ValueError("Usuário não encontrado.")

    if email and email != usuario.email:
        if obter_usuario_por_email(db, email):
            raise ValueError("E-mail já está em uso.")
        usuario.email = email

    if nome:
        usuario.nome = nome

    db.commit()
    db.refresh(usuario)
    return usuario

def alterar_situacao(db: Session, id_usuario: int, ativo: bool):
    usuario = db.query(UsuarioDB).filter(UsuarioDB.id == id_usuario).first()

    if not usuario:
        raise ValueError("Usuário não encontrado.")

    usuario.ativo = ativo
    db.commit()
    db.refresh(usuario)
    return usuario

def inativar_usuario(db: Session, id_usuario: int):
    return alterar_situacao(db, id_usuario, False)

def reativar_usuario(db: Session, id_usuario: int):
    return alterar_situacao(db, id_usuario, True)
