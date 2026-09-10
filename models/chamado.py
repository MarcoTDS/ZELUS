from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Interval, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from models.enums import StatusChamadoEnum

class ChamadoDB(Base):
    __tablename__ = "chamado"
    
    id = Column(Integer, primary_key=True, index=True)
    id_usuario_autor = Column(Integer, ForeignKey("usuario.id"))
    id_unidade_destino = Column(Integer, ForeignKey("unidade.id"), nullable=False)
    id_categoria = Column(Integer, ForeignKey("categoria_chamado.id"), nullable=False)
    titulo = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=False)
    prazo_sla_vigente = Column(Interval, nullable=False)
    status = Column(SQLEnum(StatusChamadoEnum, values_callable=lambda obj: [e.value for e in obj], name="status_chamado"))
    data_visto = Column(DateTime, nullable=True)
    data_abertura = Column(DateTime, default=datetime.utcnow)
    excluido_logicamente = Column(Boolean, default=False)
    foto_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    
    autor = relationship("UsuarioDB")

class HistoricoChamadoDB(Base):
    __tablename__ = "historico_chamado"

    id = Column(Integer, primary_key=True, index=True)
    id_chamado = Column(Integer, ForeignKey("chamado.id"), nullable=False)
    data_alteracao = Column(DateTime, default=datetime.utcnow)
    status_anterior = Column(SQLEnum(StatusChamadoEnum, values_callable=lambda obj: [e.value for e in obj], name="status_anterior"))
    novo_status = Column(SQLEnum(StatusChamadoEnum, values_callable=lambda obj: [e.value for e in obj], name="novo_status"))
    observacao = Column(Text, nullable=True)
    excluido_logicamente = Column(Boolean, default=False)