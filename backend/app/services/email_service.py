import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailService:
    async def send_verification_code(self, recipient_email: str, code: str) -> None:
        subject = "AnyAlert: підтвердження email"
        body = (
            "Вітаємо в AnyAlert!\n\n"
            f"Ваш код підтвердження: {code}\n"
            f"Код дійсний {settings.email_verification_code_ttl_minutes} хвилин.\n\n"
            "Якщо ви не створювали акаунт, проігноруйте цей лист."
        )
        await asyncio.to_thread(self._send_email_sync, recipient_email, subject, body)

    def _send_email_sync(self, recipient_email: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = f"{settings.email_from_name} <{settings.email_from}>"
        message["To"] = recipient_email
        message["Subject"] = subject
        message.set_content(body)

        timeout = float(settings.smtp_timeout_seconds)

        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=timeout) as server:
                if settings.smtp_username and settings.smtp_password:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
            return

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=timeout) as server:
            server.ehlo()
            if settings.smtp_use_starttls:
                server.starttls()
                server.ehlo()

            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)

            server.send_message(message)
