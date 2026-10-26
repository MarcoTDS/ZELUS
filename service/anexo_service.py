import os
import uuid
import jwt
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from models.chamado import ChamadoDB
from service.auth_service import SECRET_KEY, ALGORITHM
from service.chamado_service import STATUS_FINALIZADOS, _query_condominio

# Os arquivos ficam no disco do servidor; o banco guarda só o caminho relativo (foto_url / video_url).
# Sem a variável, usa a pasta "uploads" ao lado do main.py (na VPS: /opt/zelus/uploads).
PASTA_UPLOADS = Path(os.getenv("ZELUS_UPLOADS_DIR", "uploads")).resolve()

# Regra da primeira versão: no máximo 1 foto e 1 vídeo por chamado
TIPOS_ANEXO = {
    "foto": {"coluna": "foto_url", "limite_mb": 5, "nome": "A foto", "artigo": "uma foto", "formatos": "JPG, PNG ou WEBP"},
    "video": {"coluna": "video_url", "limite_mb": 50, "nome": "O vídeo", "artigo": "um vídeo", "formatos": "MP4, MOV ou WEBM"},
}

TIPOS_MIME = {
    "jpg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "mp4": "video/mp4",
    "mov": "video/quicktime",
    "webm": "video/webm",
}

VALIDADE_LINK = timedelta(hours=1)
TAMANHO_BLOCO = 1024 * 1024  # grava em blocos de 1 MB, sem carregar o vídeo inteiro na memória

def _identificar_formato(cabecalho: bytes, tipo: str):
    # Confere os primeiros bytes do arquivo (a extensão e o tipo enviados pelo navegador podem mentir)
    if tipo == "foto":
        if cabecalho.startswith(b"\xff\xd8\xff"):
            return "jpg"
        if cabecalho.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"
        if cabecalho[:4] == b"RIFF" and cabecalho[8:12] == b"WEBP":
            return "webp"
    else:
        if cabecalho[4:8] == b"ftyp":
            return "mov" if cabecalho[8:10] == b"qt" else "mp4"  # iPhone grava .mov; Android, .mp4
        if cabecalho.startswith(b"\x1a\x45\xdf\xa3"):
            return "webm"
    return None

def _caminho_seguro(caminho_relativo: str) -> Path:
    destino = (PASTA_UPLOADS / caminho_relativo).resolve()
    if PASTA_UPLOADS not in destino.parents:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")
    return destino

# ==========================================
# ENVIO (morador autor do chamado)
# ==========================================
def salvar_anexo(db: Session, id_chamado: int, tipo: str, arquivo: UploadFile, usuario: dict):
    config = TIPOS_ANEXO[tipo]

    # with_for_update: dois envios ao mesmo tempo não conseguem gravar dois arquivos no mesmo campo
    chamado = db.query(ChamadoDB).filter(
        ChamadoDB.id == id_chamado,
        ChamadoDB.ativo == True
    ).with_for_update().first()
    if not chamado or chamado.id_usuario_autor != usuario["id"]:
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")

    if chamado.status in STATUS_FINALIZADOS:
        raise HTTPException(status_code=400, detail="Não é possível anexar arquivos a um chamado resolvido ou cancelado.")

    if getattr(chamado, config["coluna"]):
        raise HTTPException(status_code=409, detail=f"Este chamado já tem {config['artigo']}. Cada chamado aceita uma foto e um vídeo.")

    origem = arquivo.file
    cabecalho = origem.read(16)
    formato = _identificar_formato(cabecalho, tipo)
    if not formato:
        raise HTTPException(status_code=415, detail=f"Formato não aceito. {config['nome']} deve ser {config['formatos']}.")

    # Nome gerado pelo sistema (o nome original do arquivo nunca vai para o disco)
    caminho_relativo = f"chamados/{chamado.id}/{tipo}-{uuid.uuid4().hex}.{formato}"
    destino = _caminho_seguro(caminho_relativo)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(destino.name + ".parcial")

    limite = config["limite_mb"] * 1024 * 1024
    tamanho = 0
    try:
        with open(temporario, "wb") as saida:
            bloco = cabecalho
            while bloco:
                tamanho += len(bloco)
                if tamanho > limite:
                    raise HTTPException(status_code=413, detail=f"{config['nome']} deve ter no máximo {config['limite_mb']} MB.")
                saida.write(bloco)
                bloco = origem.read(TAMANHO_BLOCO)
        os.replace(temporario, destino)
    finally:
        temporario.unlink(missing_ok=True)

    setattr(chamado, config["coluna"], caminho_relativo)
    try:
        db.commit()
    except Exception:
        db.rollback()
        destino.unlink(missing_ok=True)
        raise

    return {"tipo": tipo, "tamanho_bytes": tamanho}

# ==========================================
# VISUALIZAÇÃO (morador e síndico do condomínio)
# ==========================================
def gerar_link(db: Session, id_chamado: int, tipo: str, usuario: dict):
    # Mesma regra de acesso da tela de detalhes do chamado (RF18)
    chamado = _query_condominio(db, usuario["id_condominio"]).filter(ChamadoDB.id == id_chamado).first()
    if not chamado:
        raise HTTPException(status_code=404, detail="Chamado não encontrado.")

    caminho = getattr(chamado, TIPOS_ANEXO[tipo]["coluna"])
    if not caminho:
        raise HTTPException(status_code=404, detail="Este chamado não tem anexo deste tipo.")

    # Chamados antigos guardavam um link externo no lugar do arquivo
    if caminho.startswith(("http://", "https://")):
        return {"url": caminho, "externo": True}

    # <img> e <video> não enviam o token do login; por isso o link leva um token próprio, curto e só para este arquivo
    token = jwt.encode({
        "sub": "anexo",
        "caminho": caminho,
        "exp": datetime.now(timezone.utc) + VALIDADE_LINK
    }, SECRET_KEY, algorithm=ALGORITHM)
    return {"url": f"/chamados/anexos/arquivo?token={token}", "externo": False}

def abrir_arquivo(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="O link do anexo expirou. Abra o chamado novamente.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")

    if payload.get("sub") != "anexo" or not payload.get("caminho"):
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")

    destino = _caminho_seguro(payload["caminho"])
    if not destino.is_file():
        raise HTTPException(status_code=404, detail="Anexo não encontrado.")

    return destino, TIPOS_MIME.get(destino.suffix.lstrip("."), "application/octet-stream")
