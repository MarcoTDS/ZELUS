from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from database import Base
from models.enums import PerfilUsuarioEnum

class UsuarioDB(Base):
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    senha = Column(String(255), nullable=False) # Armazena a senha já criptografada (hash)
    perfil = Column(SQLEnum(PerfilUsuarioEnum, values_callable=lambda obj: [e.value for e in obj], name="perfil_usuario"), nullable=False)
    ultimo_acesso = Column(DateTime, nullable=True)
    email_validado = Column(Boolean, nullable=False, default=True)     # RN12: FALSE até o síndico validar o e-mail pelo link
    senha_provisoria = Column(Boolean, nullable=False, default=False)  # RN13: TRUE até o usuário trocar a senha provisória
    ativo = Column(Boolean, nullable=False, default=True)