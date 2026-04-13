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
        start_tls=True,  
    )


async def send_recruiter_application_email(
    *,
    recruiter_email:  str,
    recruiter_name:   str,
    job_title:        str,
    company_name:     str,
    job_id:           str,
    applicant_name:   str,
    applicant_email:  str,
    applicant_phone:  str | None,
    experience:       int,
    resume_url:       str | None,
    linkedin:         str | None,
    why_interested:   str,
) -> None:
    template  = templates.get_template("recruiter_application.html")
    html_body = template.render(
        recruiter_name  = recruiter_name,
        job_title       = job_title,
        company_name    = company_name,
        job_id          = job_id,
        applicant_name  = applicant_name,
        applicant_email = applicant_email,
        applicant_phone = applicant_phone,
        experience      = experience,
        resume_url      = resume_url,
        linkedin        = linkedin,
        why_interested  = why_interested,
    )
 
    msg = EmailMessage()
    msg["Subject"] = f"New Application: {applicant_name} → {job_title} at {company_name}"
    msg["From"]    = settings.SMTP_USER
    msg["To"]      = recruiter_email
    msg.set_content(
        f"New application from {applicant_name} for {job_title} at {company_name}.\n"
        f"Email: {applicant_email}"
    )
    msg.add_alternative(html_body, subtype="html")
 
    await aiosmtplib.send(
        msg,
        hostname  = settings.SMTP_HOST,
        port      = settings.SMTP_PORT,
        username  = settings.SMTP_USER,
        password  = settings.SMTP_PASSWORD,
        start_tls = True,
    )
 
 
async def send_jobseeker_confirmation_email(
    *,
    applicant_email: str,
    applicant_name:  str,
    job_title:       str,
    company_name:    str,
    job_id:          str,
) -> None:
    template  = templates.get_template("jobseeker_confirmation.html")
    html_body = template.render(
        applicant_name = applicant_name,
        job_title      = job_title,
        company_name   = company_name,
        job_id         = job_id,
    )
 
    msg = EmailMessage()
    msg["Subject"] = f" Application Confirmed – {job_title} at {company_name}"
    msg["From"]    = settings.SMTP_USER
    msg["To"]      = applicant_email
    msg.set_content(
        f"Hi {applicant_name}, your application for {job_title} at {company_name} "
        f"has been submitted successfully. Job ID: {job_id}"
    )
    msg.add_alternative(html_body, subtype="html")
 
    await aiosmtplib.send(
        msg,
        hostname  = settings.SMTP_HOST,
        port      = settings.SMTP_PORT,
        username  = settings.SMTP_USER,
        password  = settings.SMTP_PASSWORD,
        start_tls = True,
    )
 