import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


EMAIL_ENABLED = os.getenv(
    "EMAIL_ENABLED",
    "false"
).lower() == "true"


SMTP_HOST = os.getenv(
    "SMTP_HOST",
    "smtp.gmail.com"
)


SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "587"
    )
)


SMTP_USERNAME = os.getenv(
    "SMTP_USERNAME"
)


SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD"
)


SMTP_FROM = os.getenv(
    "SMTP_FROM"
)


def send_email(
    to_email: str,
    subject: str,
    body: str
) -> bool:

    if not EMAIL_ENABLED:
        print("Email notifications are disabled.")
        return False

    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("SMTP email configuration is missing.")
        return False

    if not SMTP_FROM:
        print("SMTP sender email is missing.")
        return False

    message = EmailMessage()

    message["From"] = SMTP_FROM
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body)

    try:
        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=10
        ) as server:

            server.starttls()

            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            server.send_message(message)

        print(
            f"Email sent successfully to {to_email}"
        )

        return True

    except Exception as error:
        print(
            f"Email sending failed: {error}"
        )

        return False