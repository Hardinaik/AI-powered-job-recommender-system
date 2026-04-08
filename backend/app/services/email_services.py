import os
from email.message import EmailMessage
import aiosmtplib
from jinja2 import Environment, FileSystemLoader
from app.config import settings


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. This moves up one level to: .../backend/app
APP_DIR = os.path.dirname(CURRENT_DIR)

# 3. This points to: .../backend/app/templates
TEMPLATE_DIR = os.path.join(APP_DIR, "templates")

templates = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


async def send_reset_email(to_email: str, reset_token: str):
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    
    # Render HTML template
    template = templates.get_template("reset_email.html")
    html_body = template.render(reset_url=reset_url, expire_minutes=15)

    msg = EmailMessage()
    msg["Subject"] = "Reset your password"
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg.set_content("Use the link to reset your password: " + reset_url)  # plain text fallback
    msg.add_alternative(html_body, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,   # STARTTLS on port 587
    )