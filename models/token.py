from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from models.enums import TipoTokenEnum

class TokenUsuarioDB(Base):
    __tablename__ = "token_usuario"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(SQLEnum(TipoTokenEnum, values_callable=lambda obj: [e.value for e in obj], name="tipo_token"), nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False) # Hash SHA-256: o token em si vai apenas no link do e-mail
    data_criacao = Column(DateTime, nullable=False, default=datetime.utcnow)
    data_expiracao = Column(DateTime, nullable=False)
    data_uso = Column(DateTime, nullable=True) # NULL = token ainda não utilizado

    usuario = relationship("UsuarioDB")