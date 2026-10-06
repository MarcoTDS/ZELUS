from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from models.enums import TipoUnidadeEnum

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
    id_sindico = Column(Integer, ForeignKey("usuario.id"), nullable=True) # NULL até o Administrador cadastrar o síndico (RN07)
    ativo = Column(Boolean, nullable=False, default=True)

    sindico = relationship("UsuarioDB")
    unidades = relationship("UnidadeDB", back_populates="condominio")

class UnidadeDB(Base):
    __tablename__ = "unidade"

    id = Column(Integer, primary_key=True, index=True)
    id_condominio = Column(Integer, ForeignKey("condominio.id"), nullable=False)
    tipo_unidade = Column(SQLEnum(TipoUnidadeEnum, values_callable=lambda obj: [e.value for e in obj], name="tipo_unidade"), nullable=False)
    bloco = Column(String(50), nullable=True)        # Apartamento
    apartamento = Column(String(50), nullable=True)  # Apartamento (obrigatório quando tipo = Apartamento)
    rua = Column(String(150), nullable=True)         # Casa
    numero_casa = Column(String(50), nullable=True)  # Casa (obrigatório quando tipo = Casa)
    descricao = Column(String(100), nullable=True)   # Área comum (obrigatório quando tipo = Area Comum)
    ativo = Column(Boolean, nullable=False, default=True)

    condominio = relationship("CondominioDB", back_populates="unidades")

    @property
    def identificacao(self) -> str:
        # Texto exibido nas telas, ex: "Bloco A, Apto 21", "Rua das Flores, Casa 5" ou "Garagem"
        if self.tipo_unidade == TipoUnidadeEnum.Apartamento:
            partes = [f"Bloco {self.bloco}" if self.bloco else None, f"Apto {self.apartamento}"]
        elif self.tipo_unidade == TipoUnidadeEnum.Casa:
            partes = [self.rua, f"Casa {self.numero_casa}"]
        else:
            partes = [self.descricao]
        return ", ".join(p for p in partes if p)