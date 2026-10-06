from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib
import secrets

from models.token import TokenUsuarioDB
from models.usuario import UsuarioDB
from models.enums import TipoTokenEnum

# Prazos de validade dos links enviados por e-mail
VALIDADE_TOKEN = {
    TipoTokenEnum.Validacao_Email: timedelta(days=2),     # RN12
    TipoTokenEnum.Redefinicao_Senha: timedelta(hours=1),  # RN16
}

def _hash_token(token: str) -> str:
    # Apenas o hash SHA-256 é armazenado; o token em si vai somente no link do e-mail
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def gerar_token(db: Session, id_usuario: int, tipo: TipoTokenEnum) -> str:
    # Um novo link invalida os anteriores do mesmo tipo ainda não utilizados (ex: "Reenviar link")
    db.query(TokenUsuarioDB).filter(
        TokenUsuarioDB.id_usuario == id_usuario,
        TokenUsuarioDB.tipo == tipo,
        TokenUsuarioDB.data_uso == None
    ).delete(synchronize_session=False)

    token = secrets.token_urlsafe(32)

    db.add(TokenUsuarioDB(
        id_usuario=id_usuario,
        tipo=tipo,
        token_hash=_hash_token(token),
        data_expiracao=datetime.utcnow() + VALIDADE_TOKEN[tipo]
    ))
    db.flush()

    return token

def consumir_token(db: Session, token: str, tipo: TipoTokenEnum) -> UsuarioDB:
    # Valida o token e o marca como utilizado (uso único). Não faz commit: quem chama decide.
    registro = db.query(TokenUsuarioDB).filter(
        TokenUsuarioDB.token_hash == _hash_token(token),
        TokenUsuarioDB.tipo == tipo
    ).first()

    if not registro or registro.data_uso is not None:
        raise ValueError("Link inválido ou já utilizado.")

    if registro.data_expiracao < datetime.utcnow():
        raise ValueError("Link expirado. Solicite um novo.")

    if not registro.usuario.ativo:
        raise ValueError("Usuário inativo.")

    registro.data_uso = datetime.utcnow()
    return registro.usuario
