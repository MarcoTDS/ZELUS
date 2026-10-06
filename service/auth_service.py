from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import os
import jwt

from models.usuario import UsuarioDB
from models.condominio import CondominioDB
from models.enums import PerfilUsuarioEnum
from service import vinculo_service

# RNF02: JWT com PyJWT (gratuito). Em produção, defina a variável de ambiente ZELUS_SECRET_KEY.
SECRET_KEY = os.getenv("ZELUS_SECRET_KEY", "zelus-chave-de-desenvolvimento-troque-em-producao")
ALGORITHM = "HS256"
EXPIRACAO_TOKEN = timedelta(hours=8)

def criar_access_token(usuario: UsuarioDB) -> str:
    payload = {
        "sub": str(usuario.id),
        "perfil": usuario.perfil.value,
        "exp": datetime.now(timezone.utc) + EXPIRACAO_TOKEN
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decodificar_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise ValueError("Sessão expirada. Faça login novamente.")
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise ValueError("Token de acesso inválido.")

def obter_id_condominio(db: Session, usuario: UsuarioDB):
    # Síndico: o condomínio que ele gerencia (RN07). Morador: o condomínio das suas unidades.
    if usuario.perfil == PerfilUsuarioEnum.Sindico:
        condominio = db.query(CondominioDB).filter(
            CondominioDB.id_sindico == usuario.id,
            CondominioDB.ativo == True
        ).first()
        return condominio.id if condominio else None

    if usuario.perfil == PerfilUsuarioEnum.Morador:
        return vinculo_service.obter_id_condominio_do_morador(db, usuario.id)

    return None # Administrador não pertence a um condomínio

def montar_usuario_atual(db: Session, token: str) -> dict:
    # Carrega o usuário a cada requisição, para que inativações tenham efeito imediato
    id_usuario = decodificar_access_token(token)

    usuario = db.query(UsuarioDB).filter(
        UsuarioDB.id == id_usuario,
        UsuarioDB.ativo == True
    ).first()
    if not usuario:
        raise ValueError("Usuário não encontrado ou inativo.")

    status_vinculo = None
    if usuario.perfil == PerfilUsuarioEnum.Morador:
        status_vinculo = vinculo_service.obter_status_vinculo(db, usuario.id)

    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "perfil": usuario.perfil.value,
        "id_condominio": obter_id_condominio(db, usuario),
        "senha_provisoria": usuario.senha_provisoria,  # RN13
        "status_vinculo": status_vinculo               # Morador pendente: o front exibe a tela de pendência
    }
