import threading
import logging

import posthog
import resend
from decouple import config

logger = logging.getLogger(__name__)

_BRAND_GREEN = "#B2E62A"
_BRAND_DARK = "#0D1117"
_BRAND_GREEN_LIGHT = "#EEF9CC"
_BRAND_GREEN_BORDER = "#D4F07A"
_BG = "#F5F6F0"


class EmailService:
    def __init__(self):
        resend.api_key = config("RESEND_API_KEY")
        self.from_email = config("RESEND_FROM_EMAIL", default="ola@suafince.com.br")

    def _send_async(self, payload: dict, user_id: int, user_email: str):
        def _send():
            try:
                resend.Emails.send(payload)
                logger.info("EmailService: email '%s' enviado para %s", payload.get("subject", ""), user_email)
                _track_email(user_id, user_email, "email_boas_vindas_enviado", {"destinatario": user_email})
            except Exception as e:
                logger.error("EmailService: falha ao enviar email para %s — %s", user_email, str(e), exc_info=True)
                _track_email(user_id, user_email, "email_boas_vindas_falha", {"destinatario": user_email, "erro": str(e)})

        thread = threading.Thread(target=_send, daemon=True)
        thread.start()

    def enviar_boas_vindas(self, user_email: str, user_name: str, user_id: int):
        payload = {
            "from": self.from_email,
            "to": [user_email],
            "subject": "Bem-vindo(a) à Fince! Seu escritório começa aqui ✨",
            "html": _template_boas_vindas(user_name),
        }
        self._send_async(payload, user_id=user_id, user_email=user_email)


def _track_email(user_id: int, user_email: str, event_name: str, properties: dict):
    try:
        if getattr(posthog, "disabled", False):
            return
        posthog.capture(
            distinct_id=str(user_id),
            event=event_name,
            properties={"user_email": user_email, **properties},
        )
    except Exception:
        pass


def _template_boas_vindas(user_name: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bem-vindo(a) à Fince!</title>
</head>
<body style="margin:0;padding:0;background-color:{_BG};font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:{_BG};">
    <tr>
      <td align="center" style="padding:40px 16px;">

        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;">

          <!-- Header dark com logo e destaque verde -->
          <tr>
            <td style="background-color:{_BRAND_DARK};border-radius:20px 20px 0 0;padding:48px 40px 44px;text-align:center;">
              <p style="margin:0 0 32px;font-size:26px;font-weight:900;color:#FFFFFF;letter-spacing:-0.5px;">Fince<span style="color:{_BRAND_GREEN};">.</span></p>
              <h1 style="margin:0 0 12px;font-size:34px;font-weight:900;color:#FFFFFF;line-height:1.2;">
                Bem-vindo(a),<br><span style="color:{_BRAND_GREEN};">{user_name}!</span> 🎉
              </h1>
              <p style="margin:0;font-size:16px;color:#9CA3AF;line-height:1.5;">
                Seu escritório financeiro começa agora.
              </p>
            </td>
          </tr>

          <!-- Body branco -->
          <tr>
            <td style="background:#FFFFFF;padding:40px 40px 32px;">

              <p style="margin:0 0 28px;font-size:16px;color:#374151;line-height:1.75;">
                Oi, <strong style="color:{_BRAND_DARK};">{user_name}</strong>! 👋<br><br>
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
                        <td style="background:{_BRAND_GREEN_LIGHT};border:1.5px solid {_BRAND_GREEN_BORDER};border-radius:12px;padding:18px 14px;text-align:center;">
                          <p style="margin:0 0 8px;font-size:26px;">💰</p>
                          <p style="margin:0 0 4px;font-size:13px;font-weight:800;color:{_BRAND_DARK};">Controle financeiro</p>
                          <p style="margin:0;font-size:12px;color:#6B7280;line-height:1.4;">Despesas, entradas e saldo em tempo real</p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td width="33%" style="padding:0 3px;vertical-align:top;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="background:{_BRAND_GREEN_LIGHT};border:1.5px solid {_BRAND_GREEN_BORDER};border-radius:12px;padding:18px 14px;text-align:center;">
                          <p style="margin:0 0 8px;font-size:26px;">🎯</p>
                          <p style="margin:0 0 4px;font-size:13px;font-weight:800;color:{_BRAND_DARK};">Motor de prioridades</p>
                          <p style="margin:0;font-size:12px;color:#6B7280;line-height:1.4;">Saiba exatamente o que pagar primeiro</p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td width="33%" style="padding:0 0 0 6px;vertical-align:top;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="background:{_BRAND_GREEN_LIGHT};border:1.5px solid {_BRAND_GREEN_BORDER};border-radius:12px;padding:18px 14px;text-align:center;">
                          <p style="margin:0 0 8px;font-size:26px;">📊</p>
                          <p style="margin:0 0 4px;font-size:13px;font-weight:800;color:{_BRAND_DARK};">Relatórios</p>
                          <p style="margin:0;font-size:12px;color:#6B7280;line-height:1.4;">Visão clara da saúde do escritório</p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Banner trial -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 32px;">
                <tr>
                  <td style="background:{_BRAND_GREEN};border-radius:14px;padding:20px 24px;">
                    <p style="margin:0 0 6px;font-size:18px;font-weight:900;color:{_BRAND_DARK};">🎁 7 dias grátis te aguardam!</p>
                    <p style="margin:0;font-size:14px;color:#374151;line-height:1.5;">
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
                       style="display:inline-block;background:{_BRAND_GREEN};color:{_BRAND_DARK};text-decoration:none;font-size:16px;font-weight:900;padding:16px 44px;border-radius:10px;letter-spacing:0.2px;">
                      Começar meu teste grátis →
                    </a>
                  </td>
                </tr>
              </table>

              <p style="margin:0;font-size:14px;color:#9CA3AF;line-height:1.6;text-align:center;">
                Alguma dúvida? Basta responder este email — nossa equipe responde rápido. 💬
              </p>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:{_BG};border-radius:0 0 20px 20px;padding:24px 40px;text-align:center;border-top:1px solid #E5E7EB;">
              <p style="margin:0 0 4px;font-size:13px;color:#9CA3AF;">
                © 2026 Fince · <a href="https://www.suafince.com.br" style="color:{_BRAND_DARK};text-decoration:none;font-weight:700;">suafince.com.br</a>
              </p>
              <p style="margin:0;font-size:12px;color:#D1D5DB;">
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
