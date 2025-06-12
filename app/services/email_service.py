import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.email_address = settings.EMAIL_ADDRESS
        self.email_password = settings.EMAIL_PASSWORD

    def send_verification_code(self, to_email: str, verification_code: str, user_name: str) -> bool:
        """
        E-posta doğrulama kodu gönderir
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = to_email
            msg["Subject"] = "Yüz Tanıma Yoklama Sistemi - E-posta Doğrulama Kodu"

            body = f"""
Merhaba {user_name},

Yüz Tanıma Yoklama Sistemi'ne hoş geldiniz!

E-posta adresinizi doğrulamak için aşağıdaki 6 haneli kodu kullanın:

🔐 DOĞRULAMA KODU: {verification_code}

Bu kod 3 dakika boyunca geçerlidir.
Maksimum 3 deneme hakkınız vardır.

Eğer bu kaydı siz yapmadıysanız, bu e-postayı dikkate almayın.

Saygılarımızla,
İstanbul Üniversitesi-Cerrahpaşa
            """

            msg.attach(MIMEText(body, "plain", "utf-8"))

            # Gmail SMTP ile gönderim
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # TLS şifreleme
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, to_email, msg.as_string())
            
            logger.info(f"Doğrulama kodu gönderildi: {to_email}")
            return True

        except Exception as e:
            logger.error(f"E-posta gönderimi başarısız: {str(e)}")
            return False

    def send_password_reset_code(self, to_email: str, reset_code: str, user_name: str) -> bool:
        """
        Şifre sıfırlama kodu gönderir
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = to_email
            msg["Subject"] = "Yüz Tanıma Yoklama Sistemi - Şifre Sıfırlama Kodu"

            body = f"""
Merhaba {user_name},

Şifrenizi sıfırlamak için aşağıdaki 6 haneli kodu kullanın:

🔐 ŞİFRE SIFIRLAMA KODU: {reset_code}

Bu kod 5 dakika boyunca geçerlidir.
Maksimum 3 deneme hakkınız vardır.

Eğer bu talebi siz yapmadıysanız, bu e-postayı dikkate almayın.

Saygılarımızla,
İstanbul Üniversitesi-Cerrahpaşa
            """

            msg.attach(MIMEText(body, "plain", "utf-8"))

            # Gmail SMTP ile gönderim
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # TLS şifreleme
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, to_email, msg.as_string())
            
            logger.info(f"Şifre sıfırlama kodu gönderildi: {to_email}")
            return True

        except Exception as e:
            logger.error(f"Şifre sıfırlama e-postası gönderimi başarısız: {str(e)}")
            return False

    def send_verification_email(self, to_email: str, verification_link: str, user_name: str) -> bool:
        """
        E-posta doğrulama linki gönderir
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = to_email
            msg["Subject"] = "Yüz Tanıma Yoklama Sistemi - E-posta Doğrulama"

            body = f"""
Merhaba {user_name},

Yüz Tanıma Yoklama Sistemi'ne hoş geldiniz!

E-posta adresinizi doğrulamak için aşağıdaki bağlantıya tıklayın:

{verification_link}

Bu link 24 saat boyunca geçerlidir.

Eğer bu kaydı siz yapmadıysanız, bu e-postayı dikkate almayın.

Saygılarımızla,
Yüz Tanıma Yoklama Sistemi
            """

            msg.attach(MIMEText(body, "plain", "utf-8"))

            # Gmail SMTP ile gönderim
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # TLS şifreleme
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, to_email, msg.as_string())
            
            logger.info(f"Doğrulama e-postası gönderildi: {to_email}")
            return True

        except Exception as e:
            logger.error(f"E-posta gönderimi başarısız: {str(e)}")
            return False

    def send_password_reset_email(self, to_email: str, reset_link: str, user_name: str) -> bool:
        """
        Şifre sıfırlama linki gönderir
        """
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = to_email
            msg["Subject"] = "Yüz Tanıma Yoklama Sistemi - Şifre Sıfırlama"

            body = f"""
Merhaba {user_name},

Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:

{reset_link}

Bu link 1 saat boyunca geçerlidir.

Eğer bu talebi siz yapmadıysanız, bu e-postayı dikkate almayın.

Saygılarımızla,
Yüz Tanıma Yoklama Sistemi
            """

            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.sendmail(self.email_address, to_email, msg.as_string())
            
            logger.info(f"Şifre sıfırlama e-postası gönderildi: {to_email}")
            return True

        except Exception as e:
            logger.error(f"Şifre sıfırlama e-postası gönderimi başarısız: {str(e)}")
            return False 