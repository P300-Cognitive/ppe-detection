"""Serviço de notificações de alertas EPI via Telegram e e-mail."""
from __future__ import annotations

import os
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, List, Optional

from src.core.models import NotificationResult

# Quando PPE_TEST_MODE=1 (definido em features/environment.py durante testes BDD),
# os envios são simulados sem chamadas reais de rede.
_TEST_MODE = lambda: os.getenv("PPE_TEST_MODE") == "1"


class NotificationService:
    """Envia notificações de violações de EPI por Telegram e/ou e-mail.

    Credenciais via variáveis de ambiente:
      TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
      EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS, EMAIL_TO
    """

    def __init__(self, channels: List[str]):
        self._channels = channels
        self._telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self._telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self._email_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self._email_port = int(os.getenv("EMAIL_PORT", "587"))
        self._email_user = os.getenv("EMAIL_USER")
        self._email_pass = os.getenv("EMAIL_PASS")
        self._email_to = os.getenv("EMAIL_TO")

    def send(self, violation: Any, image_path: Optional[str] = None) -> NotificationResult:
        result = NotificationResult()

        if "telegram" in self._channels:
            result.telegram_sent = self._send_telegram(violation, image_path)

        if "email" in self._channels:
            result.email_sent = self._send_email(violation, image_path)

        if image_path and (result.telegram_sent or result.email_sent):
            result.image_attached = True

        return result

    # ── Telegram ─────────────────────────────────────────────────────────

    def _send_telegram(self, violation: Any, image_path: Optional[str]) -> bool:
        if _TEST_MODE():
            return True
        if not self._telegram_token or not self._telegram_chat_id:
            return False
        try:
            import httpx
            msg = (
                f"⚠️ Alerta EPI: {getattr(violation, 'reason', 'não conformidade')} "
                f"| Pessoa {violation.person_id}"
            )
            base = f"https://api.telegram.org/bot{self._telegram_token}"
            if image_path and os.path.isfile(image_path):
                with open(image_path, "rb") as img:
                    httpx.post(
                        f"{base}/sendPhoto",
                        data={"chat_id": self._telegram_chat_id, "caption": msg},
                        files={"photo": img},
                    )
            else:
                httpx.post(
                    f"{base}/sendMessage",
                    json={"chat_id": self._telegram_chat_id, "text": msg},
                )
            return True
        except Exception:
            return False

    # ── E-mail ───────────────────────────────────────────────────────────

    def _send_email(self, violation: Any, image_path: Optional[str]) -> bool:
        if _TEST_MODE():
            return True
        if not all([self._email_user, self._email_pass, self._email_to]):
            return False
        try:
            msg = MIMEMultipart()
            msg["From"] = self._email_user
            msg["To"] = self._email_to
            msg["Subject"] = f"⚠️ Alerta EPI – Pessoa {violation.person_id}"
            body = (
                f"Não conformidade detectada: "
                f"{getattr(violation, 'reason', '')} "
                f"– Pessoa {violation.person_id}"
            )
            msg.attach(MIMEText(body, "plain"))
            if image_path and os.path.isfile(image_path):
                with open(image_path, "rb") as f:
                    attach = MIMEImage(f.read())
                attach.add_header(
                    "Content-Disposition", "attachment",
                    filename=os.path.basename(image_path),
                )
                msg.attach(attach)
            with smtplib.SMTP(self._email_host, self._email_port) as srv:
                srv.starttls()
                srv.login(self._email_user, self._email_pass)
                srv.send_message(msg)
            return True
        except Exception:
            return False
