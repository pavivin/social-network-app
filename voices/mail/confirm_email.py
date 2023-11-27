import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

# from voices.broker import app
from voices.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_SENDER_EMAIL,
    MAIL_PASSWORD=settings.MAIL_SENDER_PASSWORD,
    MAIL_FROM=settings.MAIL_SENDER_EMAIL,
    MAIL_PORT=settings.MAIL_SENDER_PORT,
    MAIL_SERVER=settings.MAIL_SENDER_DOMAIN,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
)


# TODO: to email class
# TODO: to file
html = """
<html>

<head></head>

<body>
    <p>Для получения доступа ко всем возможностям приложения "Мой Город"<br>
        подтвердите адрес электронной почты<br>
        <a href="voices-city.ru/api/confirm-email/{user_id}/{email_token}">Подтвердить email</a>
    </p>
</body>

</html>
""".strip()


async def async_confirm_email(user_id: str, email_token: str, recipient_email: str):
    message = MessageSchema(
        subject="Подтверждение почты",
        recipients=[recipient_email],
        body=html.format(user_id=user_id, email_token=email_token),
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)


# TODO: understand SMTP session (reuse connection, classes)
def confirm_email(user_id: str, email_token: str, recipient_email: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Подтверждение почты"
    msg["From"] = settings.MAIL_SENDER_EMAIL
    msg["To"] = recipient_email

    format_html = html.format(user_id=user_id, email_token=email_token)
    part = MIMEText(format_html, "html")

    msg.attach(part)
    mail = smtplib.SMTP(settings.MAIL_SENDER_DOMAIN, settings.MAIL_SENDER_PORT)

    mail.set_debuglevel(True)
    mail.starttls()
    mail.login(settings.MAIL_SENDER_EMAIL, settings.MAIL_SENDER_PASSWORD)
    mail.send_message(msg)
    mail.quit()


# @app.task(name="confirm_email")
# def confirm_email_task(user_id: str, email_token: str, recipient_email: str):
#     confirm_email(
#         user_id=user_id,
#         email_token=email_token,
#         recipient_email=recipient_email,
#     )
