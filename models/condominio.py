from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from models.enums import TipoCondominioEnum

class CondominioDB(Base):
    __tablename__ = "condominio"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cep = Column(String(20), nullable=False)
    numero = Column(String(6), nullable=False)
    rua = Column(String(150), nullable=False)
    bairro = Column(String(100), nullable=False)
    cidade = Column(String(100), nullable=False)
    estado = Column(String(2), nullable=False) # Sigla da UF
    id_sindico = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)

    sindico = relationship("UsuarioDB")

class UnidadeDB(Base):
    __tablename__ = "unidade"

    id = Column(Integer, primary_key=True, index=True)
    id_condominio = Column(Integer, ForeignKey("condominio.id"), nullable=False)
    tipo_condominio = Column(SQLEnum(TipoCondominioEnum, values_callable=lambda obj: [e.value for e in obj], name="tipo_condominio"), nullable=False)
    bloco = Column(String(50), nullable=True)        # Apartamento
    apartamento = Column(String(50), nullable=True)  # Apartamento (obrigatório quando tipo = Apartamento)
    rua = Column(String(150), nullable=True)         # Casa
    numero_casa = Column(String(50), nullable=True)  # Casa (obrigatório quando tipo = Casa)
    ativo = Column(Boolean, nullable=False, default=True)

    condominio = relationship("CondominioDB")