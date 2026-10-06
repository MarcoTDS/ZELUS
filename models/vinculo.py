from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

class StatusVinculoEnum(str, enum.Enum):
    Pendente = "Pendente"
    Aprovado = "Aprovado"
    Rejeitado = "Rejeitado"

class VinculoMoradorDB(Base):
    __tablename__ = "usuario_unidade"
    
    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    id_unidade = Column(Integer, ForeignKey("unidade.id"), nullable=False)
    status_aprovacao = Column(SQLEnum(StatusVinculoEnum, values_callable=lambda obj: [e.value for e in obj], name="status_aprovacao"), nullable=False, default=StatusVinculoEnum.Pendente)
    data_solicitacao = Column(DateTime, nullable=False, default=datetime.utcnow)
    data_avaliacao = Column(DateTime, nullable=True)
    ativo = Column(Boolean, nullable=False, default=True)

    usuario = relationship("UsuarioDB")
    unidade = relationship("UnidadeDB")