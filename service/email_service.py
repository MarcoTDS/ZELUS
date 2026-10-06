# RF19/RN16, RN12: Envio de e-mail SIMULADO (o projeto não envia e-mails reais).
# A mensagem é exibida no terminal do servidor (uvicorn), onde é possível copiar o link.

def enviar_email(destinatario: str, assunto: str, corpo: str):
    print("\n" + "=" * 70)
    print(f"[E-MAIL SIMULADO] Para: {destinatario}")
    print(f"Assunto: {assunto}")
    print("-" * 70)
    print(corpo)
    print("=" * 70 + "\n")
