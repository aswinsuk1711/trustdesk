import random
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from ..config import settings
from ..models import OtpStore


def _generate_otp() -> str:
    return str(random.randint(100000, 999999))


def send_otp(db: Session, email: str) -> None:
    otp = _generate_otp()
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10)

    # Delete any existing OTP for this email
    db.query(OtpStore).filter(OtpStore.email == email).delete()
    db.add(OtpStore(email=email, otp=otp, expires_at=expires_at))
    db.commit()

    if not settings.mail_username:
        # No mail config — print OTP to console for dev
        print(f"[DEV OTP] {email} → {otp}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your TrustDesk verification code"
    msg["From"] = settings.mail_from
    msg["To"] = email

    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:480px;margin:auto;padding:32px;background:#f5f2fb;border-radius:16px;">
      <h2 style="color:#28186b;margin-bottom:8px;">TrustDesk</h2>
      <p style="color:#575267;">Your one-time verification code is:</p>
      <div style="font-size:36px;font-weight:800;letter-spacing:8px;color:#4d2ea4;padding:20px 0;">{otp}</div>
      <p style="color:#858095;font-size:13px;">This code expires in 10 minutes. Do not share it with anyone.</p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
        server.starttls()
        server.login(settings.mail_username, settings.mail_password)
        server.sendmail(settings.mail_from, email, msg.as_string())


def verify_otp(db: Session, email: str, otp: str) -> bool:
    record = db.query(OtpStore).filter(OtpStore.email == email).order_by(OtpStore.id.desc()).first()
    if not record:
        return False
    if datetime.utcnow() > record.expires_at:
        db.delete(record)
        db.commit()
        return False
    if record.otp != otp:
        return False
    db.delete(record)
    db.commit()
    return True
