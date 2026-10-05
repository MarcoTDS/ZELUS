import enum

# Os valores (.value) de cada enum devem ser idênticos aos dos tipos ENUM criados no PostgreSQL

class PerfilUsuarioEnum(str, enum.Enum):
    Morador = 'Morador'
    Sindico = 'Sindico'
    Administrador = 'Administrador'

class TipoCondominioEnum(str, enum.Enum):
    Casa = 'Casa'
    Apartamento = 'Apartamento'

class StatusChamadoEnum(str, enum.Enum):
    Aberto = 'Aberto'
    Em_Andamento = 'Em Andamento'
    Resolvido = 'Resolvido'
    Cancelado = 'Cancelado'