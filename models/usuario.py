from sqlalchemy import Column, Integer, String, Boolean, Enum as SQLEnum
from database import Base
from models.enums import PerfilUsuarioEnum

class UsuarioDB(Base):
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(SQLEnum(PerfilUsuarioEnum), nullable=False)
    senha_provisoria = Column(Boolean, default=False)
    token_validacao = Column(String(255), nullable=True)
    excluido_logicamente = Column(Boolean, default=False)