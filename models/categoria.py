from sqlalchemy import Column, Integer, String, Boolean, Interval, ForeignKey
from database import Base

class CategoriaDB(Base):
    __tablename__ = "categoria_chamado"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    prazo_sla = Column(Interval, nullable=False) # Armazena como timedelta
    id_condominio = Column(Integer, ForeignKey("condominio.id"), nullable=False)
    excluido_logicamente = Column(Boolean, default=False)