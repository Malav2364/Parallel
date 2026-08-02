from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.core.mail import MailClient


class EmailService:
    def __init__(self):
        self.mail_client = MailClient()

        template_dir = Path(__file__).parent.parent / "templates"

        self.environment = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True,
        )

    def _render_template(
        self,
        template_name: str,
        **context,
    ) -> str:
        template = self.environment.get_template(
            template_name,
        )

        return template.render(
            **context,
        )

    async def send_verification_email(
        self,
        email: str,
        first_name: str,
        verification_link: str,
    ) -> None:

        html = self._render_template(
            "verify_email.html",
            first_name=first_name,
            verification_link=verification_link,
        )

        await self.mail_client.send_email(
            to_email=email,
            subject="Verify your email",
            html_content=html,
        )

    async def send_password_reset_email(
        self,
        email: str,
        first_name: str,
        reset_link: str,
    ) -> None:

        html = self._render_template(
            "reset_password.html",
            first_name=first_name,
            reset_link=reset_link,
        )

        await self.mail_client.send_email(
            to_email=email,
            subject="Reset your password",
            html_content=html,
        )
