from sqlalchemy import Column, Integer, Boolean, ForeignKey, Enum as SQLEnum, DateTime
from database import Base
from datetime import datetime
import enum

class StatusVinculoEnum(enum.Enum):
    Pendente = "Pendente"
    Aprovado = "Aprovado"
    Rejeitado = "Rejeitado"

class VinculoMoradorDB(Base):
    __tablename__ = "vinculo_morador_unidade"
    
    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    id_unidade = Column(Integer, ForeignKey("unidade.id"), nullable=False)
    status = Column(SQLEnum(StatusVinculoEnum), default=StatusVinculoEnum.Pendente)
    data_solicitacao = Column(DateTime, default=datetime.utcnow)
    data_avaliacao = Column(DateTime, nullable=True)
    id_avaliador = Column(Integer, ForeignKey("usuario.id"), nullable=True)