from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Interval, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from models.enums import StatusChamadoEnum

# Tipo ENUM "status_chamado" do PostgreSQL, compartilhado por chamado e historico_chamado
StatusChamadoType = SQLEnum(StatusChamadoEnum, values_callable=lambda obj: [e.value for e in obj], name="status_chamado")

class ChamadoDB(Base):
    __tablename__ = "chamado"
    
    id = Column(Integer, primary_key=True, index=True)
    id_usuario_autor = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    id_unidade_destino = Column(Integer, ForeignKey("unidade.id"), nullable=False)
    id_categoria = Column(Integer, ForeignKey("categoria_chamado.id"), nullable=False)
    titulo = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=False)
    foto_url = Column(String(255), nullable=True)
    video_url = Column(String(255), nullable=True)
    prazo_sla_vigente = Column(Interval, nullable=False)
    status = Column(StatusChamadoType, nullable=False, default=StatusChamadoEnum.Aberto)
    data_visto = Column(DateTime, nullable=True)
    data_abertura = Column(DateTime, nullable=False, default=datetime.utcnow)
    ativo = Column(Boolean, nullable=False, default=True)
    
    autor = relationship("UsuarioDB")
    unidade = relationship("UnidadeDB")
    categoria = relationship("CategoriaDB")
    historico = relationship("HistoricoChamadoDB", back_populates="chamado", order_by="HistoricoChamadoDB.data_alteracao")

class HistoricoChamadoDB(Base):
    __tablename__ = "historico_chamado"

    id = Column(Integer, primary_key=True, index=True)
    id_chamado = Column(Integer, ForeignKey("chamado.id"), nullable=False)
    data_alteracao = Column(DateTime, nullable=False, default=datetime.utcnow)
    status_anterior = Column(StatusChamadoType, nullable=False)
    novo_status = Column(StatusChamadoType, nullable=False)
    observacao = Column(Text, nullable=True)

    chamado = relationship("ChamadoDB", back_populates="historico")