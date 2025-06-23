# app/email_handler.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def send_verification_email(recipient_email: str, token: str):
    """Sends a verification email to the user."""
    sender_email = st.secrets.get("EMAIL_SENDER_ADDRESS")
    sender_password = st.secrets.get("EMAIL_SENDER_PASSWORD")
    
    if not sender_email or not sender_password:
        st.error("Email service is not configured. Cannot send verification email.")
        print("ERROR: Email credentials not found in secrets.")
        return False

    # Create the verification link
    # IMPORTANT: Change the base URL when deploying
    base_url = "http://localhost:8501" 
    verification_link = f"{base_url}/?verify_token={token}"

    # Create the email
    message = MIMEMultipart("alternative")
    message["Subject"] = "Verify Your Email for Cognitive Query Pro"
    message["From"] = sender_email
    message["To"] = recipient_email

    text = f"""
    Hi,
    Thank you for registering for Cognitive Query Pro!
    Please verify your email by visiting the following link:
    {verification_link}
    """
    html = f"""
    <html>
      <body>
        <div style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
          <h2>Welcome to Cognitive Query Pro!</h2>
          <p>Please click the button below to verify your email address and activate your account.</p>
          <a href="{verification_link}" style="background-color: #6c63ff; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px; font-size: 16px;">Verify Email</a>
          <p style="margin-top: 20px; font-size: 12px; color: #888;">If you cannot click the button, copy and paste this link into your browser: {verification_link}</p>
        </div>
      </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    try:
        # Connect to the SMTP server (for Gmail)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print(f"Verification email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        st.error("Failed to send verification email. Please contact support.")
        print(f"SMTP Error: {e}")
        return False