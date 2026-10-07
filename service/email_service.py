# RN12, RN13, RF19/RN16: Envio de e-mails do sistema (link de validação, senha provisória, redefinição de senha).
#
# O envio usa SMTP, configurado por variáveis de ambiente (veja o arquivo .env.example):
#   ZELUS_SMTP_HOST, ZELUS_SMTP_PORTA, ZELUS_SMTP_USUARIO, ZELUS_SMTP_SENHA, ZELUS_SMTP_REMETENTE, ZELUS_SMTP_TLS
#
# Sem ZELUS_SMTP_HOST definido, o e-mail é apenas exibido no terminal do uvicorn (modo de desenvolvimento).

import os
import smtplib
import logging
from email.message import EmailMessage

logger = logging.getLogger("zelus.email")

TIMEOUT_SMTP = 15  # segundos


def _configuracao_smtp():
    # Lida a cada envio, para que alterações no .env valham após reiniciar o uvicorn
    host = os.getenv("ZELUS_SMTP_HOST")
    if not host:
        return None

    usuario = os.getenv("ZELUS_SMTP_USUARIO")
    return {
        "host": host,
        "porta": int(os.getenv("ZELUS_SMTP_PORTA", "587")),
        "usuario": usuario,
        "senha": os.getenv("ZELUS_SMTP_SENHA"),
        "remetente": os.getenv("ZELUS_SMTP_REMETENTE") or usuario,
        "tls": os.getenv("ZELUS_SMTP_TLS", "true").lower() in ("true", "1", "sim"),
    }


def _exibir_no_terminal(destinatario: str, assunto: str, corpo: str):
    print("\n" + "=" * 70)
    print(f"[E-MAIL NÃO ENVIADO - SMTP não configurado] Para: {destinatario}")
    print(f"Assunto: {assunto}")
    print("-" * 70)
    print(corpo)
    print("=" * 70 + "\n")


def enviar_email(destinatario: str, assunto: str, corpo: str) -> bool:
    """
    Envia um e-mail em texto simples. Devolve True se o servidor SMTP aceitou a mensagem.

    Uma falha no envio NÃO interrompe a operação que chamou (cadastro do síndico, redefinição de senha):
    o erro é registrado no terminal e a função devolve False.
    """
    config = _configuracao_smtp()
    if not config:
        _exibir_no_terminal(destinatario, assunto, corpo)
        return False

    mensagem = EmailMessage()
    mensagem["From"] = f"Zelus <{config['remetente']}>"
    mensagem["To"] = destinatario
    mensagem["Subject"] = assunto
    mensagem.set_content(corpo)

    try:
        # Porta 465: conexão já criptografada (SSL). Demais portas (587): conexão comum + STARTTLS.
        if config["porta"] == 465:
            servidor = smtplib.SMTP_SSL(config["host"], config["porta"], timeout=TIMEOUT_SMTP)
        else:
            servidor = smtplib.SMTP(config["host"], config["porta"], timeout=TIMEOUT_SMTP)

        with servidor:
            if config["tls"] and config["porta"] != 465:
                servidor.starttls()
            if config["usuario"] and config["senha"]:
                servidor.login(config["usuario"], config["senha"])
            servidor.send_message(mensagem)

        logger.info("E-mail '%s' enviado para %s", assunto, destinatario)
        return True

    except (smtplib.SMTPException, OSError) as erro:
        # OSError cobre servidor fora do ar, porta bloqueada e timeout
        logger.error("Falha ao enviar o e-mail '%s' para %s: %s", assunto, destinatario, erro)
        print(f"\n[ERRO NO ENVIO DE E-MAIL] Para: {destinatario} | {assunto} | {erro}\n")
        return False
