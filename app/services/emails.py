from app.core.config import settings
from app.schemas.purchase import PurchaseRead
from app.services.mailer import Email


def site_link(path: str) -> str:
    return settings.public_url.rstrip("/") + path


def welcome_email(to: str, site_name: str) -> Email:
    return Email(
        to=to,
        subject=f"Добро пожаловать в {site_name}",
        text=(
            "Здравствуйте!\n\n"
            f"Вы зарегистрировались на сайте «{site_name}».\n"
            f"Каталог курсов: {site_link('/')}\n\n"
            "Если это были не вы, просто проигнорируйте это письмо."
        ),
    )


def password_reset_email(to: str, site_name: str, token: str) -> Email:
    minutes = settings.password_reset_expire_minutes
    return Email(
        to=to,
        subject=f"Восстановление пароля — {site_name}",
        text=(
            "Здравствуйте!\n\n"
            f"Чтобы задать новый пароль на сайте «{site_name}», перейдите по ссылке:\n"
            f"{site_link('/reset-password')}?token={token}\n\n"
            f"Ссылка действует {minutes} минут и сработает один раз.\n"
            "Если вы не запрашивали восстановление, просто проигнорируйте письмо — пароль не изменится."
        ),
    )


def purchase_email(purchase: PurchaseRead, site_name: str) -> Email:
    item = (
        f"модулю «{purchase.module_title}» курса «{purchase.course_title}»"
        if purchase.module_title
        else f"курсу «{purchase.course_title}»"
    )
    return Email(
        to=purchase.user_email,
        subject=f"Доступ открыт — {purchase.course_title}",
        text=(
            "Здравствуйте!\n\n"
            f"Вам открыт доступ к {item}.\n"
            f"Начать обучение: {site_link(f'/courses/{purchase.course_slug}')}\n\n"
            f"Номер операции: {purchase.payment_reference}\n"
            f"С уважением, «{site_name}»"
        ),
    )
