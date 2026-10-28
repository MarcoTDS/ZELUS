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

# URL do front-end usada nos links enviados por e-mail (em produção: ZELUS_URL_FRONTEND no .env)
URL_FRONTEND = os.getenv("ZELUS_URL_FRONTEND", "http://127.0.0.1:5501").rstrip("/")

# RNF04: Hash de senha com bcrypt (usado diretamente, pois o passlib 1.7.4 é incompatível com o bcrypt 5.x)
# Atenção: o bcrypt aceita no máximo 72 bytes de senha

def obter_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha_plana.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
        # Senha acima de 72 bytes ou hash inválido
        return False

# ==========================================
# CONSULTAS
# ==========================================
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
    # Sem filtro de "ativo": o e-mail é UNIQUE no banco, inclusive para usuários inativados
    return db.query(UsuarioDB).filter(UsuarioDB.email == email).first()

# ==========================================
# AUTENTICAÇÃO (RF01, RN12, RN13)
# ==========================================
def autenticar_usuario(db: Session, email: str, senha_plana: str):
    usuario = obter_usuario_por_email(db, email)
    if not usuario or not verificar_senha(senha_plana, usuario.senha):
        return None

    if not usuario.ativo:
        # Morador removido de todas as unidades: a conta é reaproveitada pela Tela de Cadastro
        if vinculo_service.morador_sem_unidade(db, usuario):
            raise PermissionError("Sua conta não está vinculada a nenhuma unidade. Para solicitar uma nova, acesse \"Cadastre-se\" e informe este mesmo e-mail.")
        return None

    # RN12: O síndico só acessa após validar o e-mail pelo link
    if not usuario.email_validado:
        raise PermissionError("E-mail ainda não validado. Acesse o link enviado para o seu e-mail.")

    # Registra a data e hora do login com sucesso
    usuario.ultimo_acesso = datetime.utcnow()
    db.commit()
    db.refresh(usuario)
        
    return usuario

def validar_email(db: Session, token: str):
    # RN12: Confirma o e-mail do síndico através do link
    usuario = token_service.consumir_token(db, token, TipoTokenEnum.Validacao_Email)
    usuario.email_validado = True
    db.commit()
    db.refresh(usuario)
    return usuario

# ==========================================
# CADASTRO DO MORADOR (RF05, RF06, RN11)
# ==========================================
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
    # Tela de Cadastro: decide quais campos são exibidos depois que o e-mail é digitado
    usuario = obter_usuario_por_email(db, email)
    if not usuario:
        return "novo"          # Exibe nome, senha, condomínio e unidade
    if vinculo_service.morador_sem_unidade(db, usuario):
        return "sem_unidade"   # Conta reaproveitada: exibe senha atual, condomínio e unidade
    return "existente"         # Conta em uso: o usuário deve entrar pelo login

def cadastrar_morador(db: Session, dados: CadastroMoradorRequest):
    usuario = obter_usuario_por_email(db, dados.email)

    if usuario:
        # RN11: E-mail de uma conta em uso bloqueia a solicitação.
        # Exceção: morador sem unidade reaproveita a própria conta, confirmando a senha atual.
        if not vinculo_service.morador_sem_unidade(db, usuario):
            raise ValueError("Já existe uma conta cadastrada com este e-mail.")
        if not verificar_senha(dados.senha, usuario.senha):
            raise HTTPException(status_code=401, detail="Senha incorreta. Informe a senha da sua conta.")
        usuario.ativo = True # Fica ativo, mas só acessa o sistema após a aprovação do síndico
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

    # RF06: Uma solicitação por unidade, pendente até a aprovação do síndico (tudo na mesma transação)
    try:
        vinculos = [
            vinculo_service.criar_solicitacao(db, novo_usuario.id, id_unidade)
            for id_unidade in dict.fromkeys(dados.ids_unidades) # ignora unidades repetidas
        ]
    except Exception:
        db.rollback() # Alguma unidade inválida: nada é criado nem reativado
        raise

    db.commit()
    db.refresh(novo_usuario)
    for vinculo in vinculos:
        db.refresh(vinculo)
    return novo_usuario, vinculos

# ==========================================
# SENHA (RF15, RF16, RF19, RN13, RN16)
# ==========================================
def alterar_senha(db: Session, id_usuario: int, senha_atual: str, nova_senha: str):
    usuario = buscar_por_id(db, id_usuario)
    
    if not usuario:
        raise ValueError("Usuário não encontrado.")
        
    if not verificar_senha(senha_atual, usuario.senha):
        raise ValueError("A senha atual informada está incorreta.")

    if senha_atual == nova_senha:
        raise ValueError("A nova senha deve ser diferente da senha atual.")
        
    usuario.senha = obter_hash_senha(nova_senha)
    usuario.senha_provisoria = False # RN13: Libera o acesso ao restante do sistema
    
    db.commit()
    db.refresh(usuario)
    return usuario

def solicitar_redefinicao_senha(db: Session, email: str):
    # RF19/RN16: Por segurança, a resposta ao usuário é a mesma exista ou não o e-mail
    usuario = obter_usuario_por_email(db, email)
    # Morador sem unidade também recebe o link: ele precisa da senha para pedir nova unidade no cadastro
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
    usuario.email_validado = True # O link recebido por e-mail também comprova a posse do e-mail

    db.commit()
    db.refresh(usuario)
    return usuario

# ==========================================
# PERFIL E INATIVAÇÃO (RF15, RF21, RN08)
# ==========================================
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
    # Soft Delete (RN08): o registro permanece no banco com ativo = FALSE
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
