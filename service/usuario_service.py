from sqlalchemy.orm import Session
from passlib.context import CryptContext
from models.usuario import UsuarioDB
from schemas.usuario import UsuarioCreate

# RNF04: Configuração do passlib para usar bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def obter_hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha_plana, senha_hash)

def buscar_por_email(db: Session, email: str):
    return db.query(UsuarioDB).filter(
        UsuarioDB.email == email, 
        UsuarioDB.excluido_logicamente == False
    ).first()

def autenticar_usuario(db: Session, email: str, senha_plana: str):
    usuario = buscar_por_email(db, email)
    if not usuario:
        return None
    
    if not verificar_senha(senha_plana, usuario.senha_hash):
        return None
        
    return usuario

def alterar_senha(db: Session, id_usuario: int, senha_atual: str, nova_senha: str):
    usuario = db.query(UsuarioDB).filter(
        UsuarioDB.id == id_usuario, 
        UsuarioDB.excluido_logicamente == False
    ).first()
    
    if not usuario:
        raise ValueError("Usuário não encontrado.")
        
    if not verificar_senha(senha_atual, usuario.senha_hash):
        raise ValueError("A senha atual informada está incorreta.")
        
    # Atualiza a senha e remove a obrigatoriedade de troca se for o primeiro login (RN13)
    usuario.senha_hash = obter_hash_senha(nova_senha)
    usuario.senha_provisoria = False
    
    db.commit()
    db.refresh(usuario)
    return usuario

def atualizar_perfil(db: Session, id_usuario: int, novo_email: str):
    usuario = db.query(UsuarioDB).filter(
        UsuarioDB.id == id_usuario, 
        UsuarioDB.excluido_logicamente == False
    ).first()
    
    if not usuario:
        raise ValueError("Usuário não encontrado.")
        
    usuario.email = novo_email
    db.commit()
    db.refresh(usuario)
    return usuario

def obter_usuario_por_email(db: Session, email: str):
    return db.query(UsuarioDB).filter(UsuarioDB.email == email).first()

def criar_usuario(db: Session, usuario: UsuarioCreate):
    hash_senha = obter_hash_senha(usuario.senha)
    
    db_usuario = UsuarioDB(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=hash_senha,
        perfil=usuario.perfil or "Morador"
    )
    
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario