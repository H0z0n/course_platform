import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from starlette.concurrency import run_in_threadpool

from app.core.config import settings

logger = logging.getLogger("app.mail")


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    text: str


def build_message(email: Email) -> EmailMessage:
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = email.to
    message["Subject"] = email.subject
    message.set_content(email.text)
    return message


def send_via_smtp(message: EmailMessage) -> None:
    smtp_class = smtplib.SMTP_SSL if settings.smtp_ssl else smtplib.SMTP
    with smtp_class(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_starttls and not settings.smtp_ssl:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password or "")
        smtp.send_message(message)


async def deliver(email: Email) -> None:
    if not settings.smtp_host:
        logger.warning(
            "SMTP не настроен — письмо не отправлено.\nКому: %s\nТема: %s\n\n%s",
            email.to,
            email.subject,
            email.text,
        )
        return
    try:
        await run_in_threadpool(send_via_smtp, build_message(email))
    except (smtplib.SMTPException, OSError):
        logger.exception("Не удалось отправить письмо на %s", email.to)
