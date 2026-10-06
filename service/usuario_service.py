from sqlalchemy.orm import Session
import bcrypt
from datetime import datetime
from models.usuario import UsuarioDB
from models.enums import PerfilUsuarioEnum, TipoTokenEnum
from schemas.usuario import UsuarioCreate, CadastroMoradorRequest
from service import token_service, vinculo_service
from service.email_service import enviar_email

# URL do front-end usada nos links enviados por e-mail
URL_FRONTEND = "http://127.0.0.1:5500"

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
    usuario = buscar_por_email(db, email)
    if not usuario or not verificar_senha(senha_plana, usuario.senha):
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

def cadastrar_morador(db: Session, dados: CadastroMoradorRequest):
    # RN11: E-mail que já corresponde a uma conta existente bloqueia a solicitação
    if obter_usuario_por_email(db, dados.email):
        raise ValueError("Já existe uma conta cadastrada com este e-mail.")

    novo_usuario = UsuarioDB(
        nome=dados.nome,
        email=dados.email,
        senha=obter_hash_senha(dados.senha),
        perfil=PerfilUsuarioEnum.Morador
    )
    db.add(novo_usuario)
    db.flush()

    # RF06: O cadastro fica pendente até a aprovação do síndico (usuário e vínculo na mesma transação)
    try:
        vinculo = vinculo_service.criar_solicitacao(db, novo_usuario.id, dados.id_unidade)
    except Exception:
        db.rollback() # Unidade inválida: o usuário também não é criado
        raise

    db.commit()
    db.refresh(novo_usuario)
    db.refresh(vinculo)
    return novo_usuario, vinculo

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
    usuario = buscar_por_email(db, email)
    if not usuario:
        return

    token = token_service.gerar_token(db, usuario.id, TipoTokenEnum.Redefinicao_Senha)
    db.commit()

    enviar_email(
        usuario.email,
        "Zelus - Redefinição de senha",
        f"Olá, {usuario.nome}!\n\nPara definir uma nova senha, acesse o link abaixo (válido por 1 hora):\n"
        f"{URL_FRONTEND}/redefinir-senha.html?token={token}"
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
