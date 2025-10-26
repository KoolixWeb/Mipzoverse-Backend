import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
from database import email_templates_collection
import logging

logger = logging.getLogger(__name__)

async def get_email_template(template_name: str):
    """Retrieve email template from database"""
    template = await email_templates_collection.find_one({"template_name": template_name})
    if not template:
        raise ValueError(f"Email template '{template_name}' not found")
    return template

def render_template(content: str, variables: dict):
    """Replace template variables with actual values"""
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        content = content.replace(placeholder, str(value))
    return content

async def send_reset_code_email(email: str, reset_code: str):
    """Send password reset code via email"""
    try:
        # Get template from database
        template = await get_email_template("reset_password")
        
        # Prepare variables
        variables = {
            "RESET_CODE": reset_code
        }
        
        # Render templates
        html_content = render_template(template["html_content"], variables)
        text_content = render_template(template["text_content"], variables)
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = template["subject"]
        message["From"] = settings.smtp_from_email
        message["To"] = email

        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        message.attach(part1)
        message.attach(part2)

        # Send email
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, email, message.as_string())
        
        logger.info(f"Reset code email sent to {email}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {str(e)}")
        return False