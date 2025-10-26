import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
import logging

logger = logging.getLogger(__name__)

def send_reset_code_email(email: str, reset_code: str):
    """Send password reset code via email"""
    try:
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Password Reset Code"
        message["From"] = settings.smtp_from_email
        message["To"] = email

        # HTML email body
        html = f"""
        <html>
          <body>
            <h2>Password Reset Request</h2>
            <p>You requested to reset your password. Use the code below to reset your password:</p>
            <h1 style="color: #4CAF50; letter-spacing: 5px;">{reset_code}</h1>
            <p>This code will expire in 15 minutes.</p>
            <p>If you didn't request this, please ignore this email.</p>
          </body>
        </html>
        """

        # Plain text fallback
        text = f"""
        Password Reset Request
        
        You requested to reset your password. Use the code below to reset your password:
        
        {reset_code}
        
        This code will expire in 15 minutes.
        
        If you didn't request this, please ignore this email.
        """

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
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