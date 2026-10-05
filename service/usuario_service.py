from sqlalchemy.orm import Session
import bcrypt
from datetime import datetime
from models.usuario import UsuarioDB
from models.enums import PerfilUsuarioEnum
from schemas.usuario import UsuarioCreate

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

def buscar_por_email(db: Session, email: str):
    return db.query(UsuarioDB).filter(
        UsuarioDB.email == email, 
        UsuarioDB.ativo == True
    ).first()

def autenticar_usuario(db: Session, email: str, senha_plana: str):
    usuario = buscar_por_email(db, email)
    if not usuario:
        return None
    
    if not verificar_senha(senha_plana, usuario.senha):
        return None

    # Indica se é o primeiro login do usuário (ultimo_acesso ainda vazio)
    primeiro_acesso = usuario.ultimo_acesso is None

    # Registra a data e hora do login com sucesso
    usuario.ultimo_acesso = datetime.utcnow()
    db.commit()
    db.refresh(usuario)

    # Atributo dinâmico (não persistido), no mesmo padrão do "vencido" dos chamados
    usuario.primeiro_acesso = primeiro_acesso
        
    return usuario

def alterar_senha(db: Session, id_usuario: int, senha_atual: str, nova_senha: str):
    usuario = db.query(UsuarioDB).filter(
        UsuarioDB.id == id_usuario, 
        UsuarioDB.ativo == True
    ).first()
    
    if not usuario:
        raise ValueError("Usuário não encontrado.")
        
    if not verificar_senha(senha_atual, usuario.senha):
        raise ValueError("A senha atual informada está incorreta.")
        
    usuario.senha = obter_hash_senha(nova_senha)
    
    db.commit()
    db.refresh(usuario)
    return usuario

def atualizar_perfil(db: Session, id_usuario: int, novo_email: str):
    usuario = db.query(UsuarioDB).filter(
        UsuarioDB.id == id_usuario, 
        UsuarioDB.ativo == True
    ).first()
    
    if not usuario:
        raise ValueError("Usuário não encontrado.")
        
    usuario.email = novo_email
    db.commit()
    db.refresh(usuario)
    return usuario

def obter_usuario_por_email(db: Session, email: str):
    # Sem filtro de "ativo": o e-mail é UNIQUE no banco, inclusive para usuários inativados
    return db.query(UsuarioDB).filter(UsuarioDB.email == email).first()

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

def inativar_usuario(db: Session, id_usuario: int):
    # Soft Delete: o registro permanece no banco com ativo = FALSE
    usuario = db.query(UsuarioDB).filter(
        UsuarioDB.id == id_usuario, 
        UsuarioDB.ativo == True
    ).first()

    if not usuario:
        raise ValueError("Usuário não encontrado.")

    usuario.ativo = False
    db.commit()
    db.refresh(usuario)
    return usuario