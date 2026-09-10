import enum

class PerfilUsuarioEnum(str, enum.Enum):
    Morador = 'Morador'
    Sindico = 'Sindico'
    Administrador = 'Administrador'

class StatusChamadoEnum(str, enum.Enum):
    Aberto = 'Aberto'
    Em_Andamento = 'Em Andamento'
    Resolvido = 'Resolvido'
    Cancelado = 'Cancelado'