import threading
import logging

import resend
from decouple import config

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        resend.api_key = config("RESEND_API_KEY")
        self.from_email = config("RESEND_FROM_EMAIL", default="ola@suafince.com.br")

    def _send_async(self, **kwargs):
        def _send():
            try:
                resend.Emails.send(kwargs)
            except Exception as e:
                logger.error("EmailService: falha ao enviar email — %s", str(e), exc_info=True)

        thread = threading.Thread(target=_send, daemon=True)
        thread.start()

    def enviar_boas_vindas(self, user_email: str, user_name: str):
        self._send_async(
            **{
                "from": self.from_email,
                "to": [user_email],
                "subject": "Bem-vindo(a) à Fince! Seu escritório começa aqui ✨",
                "html": _template_boas_vindas(user_name),
            }
        )


def _template_boas_vindas(user_name: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bem-vindo(a) à Fince!</title>
</head>
<body style="margin:0;padding:0;background-color:#F4F2FF;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#F4F2FF;">
    <tr>
      <td align="center" style="padding:40px 16px;">

        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;">

          <!-- Header gradiente -->
          <tr>
            <td style="background:linear-gradient(135deg,#5B3DF5 0%,#7C5CFC 100%);border-radius:20px 20px 0 0;padding:48px 40px 40px;text-align:center;">
              <p style="margin:0 0 8px;font-size:28px;font-weight:800;color:#FFFFFF;letter-spacing:-0.5px;">✨ Fince</p>
              <h1 style="margin:24px 0 8px;font-size:32px;font-weight:800;color:#FFFFFF;line-height:1.2;">
                Bem-vindo(a), {user_name}! 🎉
              </h1>
              <p style="margin:0;font-size:17px;color:#D4C9FF;line-height:1.5;">
                Seu escritório financeiro começa aqui.
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="background:#FFFFFF;padding:40px 40px 32px;">

              <p style="margin:0 0 28px;font-size:16px;color:#3D3D5C;line-height:1.7;">
                Oi, <strong>{user_name}</strong>! 👋<br><br>
                Ficamos muito felizes em ter você por aqui. A Fince foi criada para que
                advogados e escritórios de advocacia tenham controle total das suas finanças —
                sem planilhas complicadas, sem perda de tempo.
              </p>

              <!-- 3 cards de feature -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 28px;">
                <tr>
                  <td width="33%" style="padding:0 6px 0 0;vertical-align:top;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="background:#F4F2FF;border:1px solid #E8E4FE;border-radius:12px;padding:18px 14px;text-align:center;">
                          <p style="margin:0 0 8px;font-size:26px;">💰</p>
                          <p style="margin:0 0 4px;font-size:13px;font-weight:700;color:#5B3DF5;">Controle financeiro</p>
                          <p style="margin:0;font-size:12px;color:#6B6B8D;line-height:1.4;">Despesas, entradas e saldo em tempo real</p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td width="33%" style="padding:0 3px;vertical-align:top;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="background:#F4F2FF;border:1px solid #E8E4FE;border-radius:12px;padding:18px 14px;text-align:center;">
                          <p style="margin:0 0 8px;font-size:26px;">🎯</p>
                          <p style="margin:0 0 4px;font-size:13px;font-weight:700;color:#5B3DF5;">Motor de prioridades</p>
                          <p style="margin:0;font-size:12px;color:#6B6B8D;line-height:1.4;">Saiba exatamente o que pagar primeiro</p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td width="33%" style="padding:0 0 0 6px;vertical-align:top;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="background:#F4F2FF;border:1px solid #E8E4FE;border-radius:12px;padding:18px 14px;text-align:center;">
                          <p style="margin:0 0 8px;font-size:26px;">📊</p>
                          <p style="margin:0 0 4px;font-size:13px;font-weight:700;color:#5B3DF5;">Relatórios</p>
                          <p style="margin:0;font-size:12px;color:#6B6B8D;line-height:1.4;">Visão clara da saúde do escritório</p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Banner trial -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 32px;">
                <tr>
                  <td style="background:linear-gradient(135deg,#EDE9FF 0%,#F0EBFF 100%);border:1.5px solid #C4B5FD;border-radius:14px;padding:20px 24px;">
                    <p style="margin:0 0 6px;font-size:18px;font-weight:800;color:#5B3DF5;">🎁 7 dias grátis te aguardam!</p>
                    <p style="margin:0;font-size:14px;color:#6B6B8D;line-height:1.5;">
                      Explore tudo sem precisar cadastrar cartão de crédito.<br>
                      Quando estiver pronto, escolha o plano que faz sentido pro seu escritório.
                    </p>
                  </td>
                </tr>
              </table>

              <!-- CTA -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 32px;">
                <tr>
                  <td align="center">
                    <a href="https://www.suafince.com.br/app"
                       style="display:inline-block;background:#5B3DF5;color:#FFFFFF;text-decoration:none;font-size:16px;font-weight:700;padding:16px 40px;border-radius:10px;letter-spacing:0.2px;">
                      Começar agora →
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0;font-size:14px;color:#9090A8;line-height:1.6;text-align:center;">
                Alguma dúvida? Basta responder este email — nossa equipe responde rápido. 💬
              </p>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#F4F2FF;border-radius:0 0 20px 20px;padding:24px 40px;text-align:center;border-top:1px solid #E8E4FE;">
              <p style="margin:0 0 4px;font-size:13px;color:#9090A8;">
                © 2026 Fince · <a href="https://www.suafince.com.br" style="color:#5B3DF5;text-decoration:none;">suafince.com.br</a>
              </p>
              <p style="margin:0;font-size:12px;color:#B0B0C8;">
                Você recebeu este email por criar uma conta na Fince.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>
"""
