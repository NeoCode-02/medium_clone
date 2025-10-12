import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from celery import Celery

from app.core.config import settings

celery = Celery(
    "email_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)


@celery.task(name="send_email_code_email")
def send_email_code_email(email: str, code: str, purpose: str):
    """
    Sends a 6-digit code via email for verification or password reset.
    purpose: 'verify' or 'reset'
    """

    if purpose == "verify":
        subject = "Verify your MediumClone account"
        body = f"""
        <h2>Welcome to {settings.APP_NAME}!</h2>
        <p>Your verification code is:</p>
        <h1 style="color:#2b6cb0;">{code}</h1>
        <p>This code will expire in 2 minutes.</p>
        """
    elif purpose == "reset":
        subject = "Password Reset Request"
        body = f"""
        <h2>Password Reset for {settings.APP_NAME}</h2>
        <p>Here is your reset code:</p>
        <h1 style="color:#e53e3e;">{code}</h1>
        <p>This code will expire in 2 minutes.</p>
        """
    else:
        raise ValueError("Invalid purpose. Expected 'verify' or 'reset'.")

    # Create MIME email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    msg["To"] = email
    msg.attach(MIMEText(body, "html"))

    # Send email via SMTP
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.MAIL_FROM, [email], msg.as_string())
    except Exception as e:
        print(f"❌ Failed to send email to {email}: {e}")
        raise e

    print(f"✅ Email sent to {email} for {purpose}.")
