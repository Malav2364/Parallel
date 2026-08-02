from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings


class MailClient:
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> None:

        message = EmailMessage()

        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
        message["To"] = to_email
        message["Subject"] = subject

        message.set_content("Please use an HTML compatible email client.")

        message.add_alternative(
            html_content,
            subtype="html",
        )

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_USE_TLS,
        )
