from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class CondominioDB(Base):
    __tablename__ = "condominio"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    endereco = Column(String(255), nullable=False)
    id_sindico = Column(Integer, ForeignKey("usuario.id"), nullable=True)
    excluido_logicamente = Column(Boolean, default=False)

class UnidadeDB(Base):
    __tablename__ = "unidade"

    id = Column(Integer, primary_key=True, index=True)
    id_condominio = Column(Integer, ForeignKey("condominio.id"), nullable=False)
    bloco = Column(String(50), nullable=True)
    numero = Column(String(50), nullable=False)
    excluido_logicamente = Column(Boolean, default=False)

class SindicoCondominioDB(Base):
    __tablename__ = "sindico_condominio"
    
    id = Column(Integer, primary_key=True, index=True)
    id_usuario_sindico = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    id_condominio = Column(Integer, ForeignKey("condominio.id"), nullable=False)
    excluido_logicamente = Column(Boolean, default=False)