import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from voices.config import settings

# TODO: to email class
# TODO: to file
html = """
<html>

<head></head>

<body>
    <p>Для получения доступа ко всем возможностям приложения "Мой Ярославль"<br>
        подтвердите адрес электронной почты<br>
        <a href="voices-city.ru/api/confirm-email/{user_id}/{email_token}">Подтвердить email</a>
    </p>
</body>

</html>
""".strip()


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

    mail.ehlo()

    mail.starttls()

    mail.login(user=settings.MAIL_SENDER_EMAIL, password=settings.MAIL_SENDER_PASSWORD)
    mail.sendmail(settings.MAIL_SENDER_EMAIL, recipient_email, msg.as_string())
    mail.quit()
