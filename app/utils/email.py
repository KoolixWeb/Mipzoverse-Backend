import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from config import settings
from database import email_templates_collection
import logging
import os
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_logo_path():
    """Get the absolute path to the logo file"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logo_path = os.path.join(base_dir, "static", "logo.png")
    
    if os.path.exists(logo_path):
        logger.info(f"Logo found at: {logo_path}")
        return logo_path
    else:
        logger.warning(f"Logo not found at: {logo_path}")
        return None

async def get_email_template(template_name: str):
    """Retrieve email template from database"""
    template = await email_templates_collection.find_one({"template_name": template_name})
    if not template:
        raise ValueError(f"Email template '{template_name}' not found")
    return template

def render_template(content: str, variables: dict):
    """Replace template variables with actual values - supports {{VAR}} format"""
    def replacer(match):
        var_name = match.group(1).strip()
        return str(variables.get(var_name, match.group(0)))
    
    # Replace {{VARIABLE_NAME}} with values
    content = re.sub(r'\{\{(\w+)\}\}', replacer, content)
    return content

async def send_reset_code_email(email: str, reset_code: str):
    """Send password reset code via email with embedded logo using CID"""
    try:
        logger.info(f"Attempting to send reset code email to {email}")
        
        # Get template from database
        template = await get_email_template("reset_password")
        logger.info(f"Retrieved email template: {template['template_name']}")
        
        # Use CID reference for logo (this is more reliable than base64 in emails)
        logo_cid = "company_logo_12345"
        
        # Prepare variables - use CID instead of base64
        variables = {
            "RESET_CODE": reset_code,
            "LOGO_URL": f"cid:{logo_cid}"
        }
        
        # Render templates
        html_content = render_template(template["html_content"], variables)
        text_content = render_template(template["text_content"], variables)
        
        logger.info(f"Templates rendered successfully")
        
        # Create multipart message with related parts (for inline images)
        message = MIMEMultipart("related")
        message["Subject"] = template["subject"]
        message["From"] = settings.smtp_from_email
        message["To"] = email

        # Create alternative part for text and HTML
        msg_alternative = MIMEMultipart("alternative")
        message.attach(msg_alternative)

        # Attach text and HTML versions
        part_text = MIMEText(text_content, "plain", "utf-8")
        part_html = MIMEText(html_content, "html", "utf-8")
        msg_alternative.attach(part_text)
        msg_alternative.attach(part_html)

        # Attach logo image with CID
        logo_path = get_logo_path()
        if logo_path and os.path.exists(logo_path):
            with open(logo_path, "rb") as img_file:
                img_data = img_file.read()
                img = MIMEImage(img_data)
                img.add_header('Content-ID', f'<{logo_cid}>')
                img.add_header('Content-Disposition', 'inline', filename='logo.png')
                message.attach(img)
                logger.info(f"Logo attached with CID: {logo_cid}")
        else:
            logger.warning("Logo file not found, email will be sent without logo")

        # Send email
        logger.info(f"Connecting to SMTP server: {settings.smtp_server}:{settings.smtp_port}")
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.set_debuglevel(0)  # Set to 1 for SMTP debugging
            server.starttls()
            logger.info("STARTTLS successful")
            server.login(settings.smtp_username, settings.smtp_password)
            logger.info("SMTP login successful")
            server.sendmail(settings.smtp_from_email, email, message.as_string())
            logger.info(f"✓ Reset code email sent successfully to {email}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Failed to send email to {email}: {str(e)}", exc_info=True)
        return False