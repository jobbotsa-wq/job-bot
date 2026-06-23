import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def send_summary_email(gmail_config: dict, user_name: str, to_email: str, results: dict):
    sender = gmail_config["sender_email"]
    app_password = gmail_config["app_password"]

    applied = results.get("applied", [])
    skipped = results.get("skipped", [])
    errors = results.get("errors", [])

    subject = f"[Job Bot] Resumen semanal — {datetime.now().strftime('%d/%m/%Y')}"

    html = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #0077b5;">📋 Resumen de aplicaciones — {user_name}</h2>
    <p style="color: #666;">Semana del {datetime.now().strftime('%d/%m/%Y')}</p>

    <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #2e7d32; margin: 0 0 10px 0;">✅ Aplicaciones enviadas ({len(applied)})</h3>
        {"".join(f'''
        <div style="border-bottom: 1px solid #c8e6c9; padding: 8px 0;">
            <strong>{job['title']}</strong> — {job['company']}<br>
            <span style="color: #666; font-size: 0.9em;">Score: {job.get('match_score', 0)}% |
            <a href="{job['url']}">Ver oferta</a></span>
        </div>''' for job in applied) if applied else "<p>Ninguna esta semana</p>"}
    </div>

    <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #e65100; margin: 0 0 10px 0;">🔗 Links externos — requieren aplicación manual ({len(skipped)})</h3>
        {"".join(f'''
        <div style="border-bottom: 1px solid #ffe0b2; padding: 8px 0;">
            <strong>{job['title']}</strong> — {job['company']}<br>
            <a href="{job['url']}" style="font-size: 0.9em;">Aplicar manualmente →</a>
        </div>''' for job in skipped) if skipped else "<p>Ninguna</p>"}
    </div>

    {"" if not errors else f'''
    <div style="background: #fce4ec; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #c62828; margin: 0 0 10px 0;">⚠️ Errores ({len(errors)})</h3>
        {"".join(f"<p>{e}</p>" for e in errors)}
    </div>'''}

    <p style="color: #999; font-size: 0.8em; margin-top: 20px;">
        Próxima ejecución: lunes siguiente a las 9:00 AM
    </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.sendmail(sender, to_email, msg.as_string())
        print(f"[Email] Resumen enviado a {to_email}")
    except Exception as e:
        print(f"[Email] Error enviando resumen: {e}")
