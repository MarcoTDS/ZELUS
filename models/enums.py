import enum

# Os valores (.value) de cada enum devem ser idênticos aos dos tipos ENUM criados no PostgreSQL

class PerfilUsuarioEnum(str, enum.Enum):
    Morador = 'Morador'
    Sindico = 'Sindico'
    Administrador = 'Administrador'

class TipoUnidadeEnum(str, enum.Enum):
    Casa = 'Casa'
    Apartamento = 'Apartamento'
    Area_Comum = 'Area Comum'

class StatusChamadoEnum(str, enum.Enum):
    Aberto = 'Aberto'
    Em_Andamento = 'Em Andamento'
    Resolvido = 'Resolvido'
    Cancelado = 'Cancelado'

class TipoTokenEnum(str, enum.Enum):
    Validacao_Email = 'Validacao Email'
    Redefinicao_Senha = 'Redefinicao Senha'