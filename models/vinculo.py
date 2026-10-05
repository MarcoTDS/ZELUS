from sqlalchemy import Column, Integer, Boolean, ForeignKey, Enum as SQLEnum
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
    ativo = Column(Boolean, nullable=False, default=True)