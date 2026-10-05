from sqlalchemy import Column, Integer, String, Boolean, Interval, ForeignKey
from database import Base

class CategoriaDB(Base):
    __tablename__ = "categoria_chamado"
    
    id = Column(Integer, primary_key=True, index=True)
    id_condominio = Column(Integer, ForeignKey("condominio.id"), nullable=False)
    nome = Column(String(100), nullable=False)
    prazo_sla = Column(Interval, nullable=False) # Armazena como timedelta
    ativo = Column(Boolean, nullable=False, default=True)