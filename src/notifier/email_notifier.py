import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger("jobbot")


def send_summary_email(gmail_config: dict, user_name: str, to_email: str, results: dict):
    sender = gmail_config.get("sender_email", "")
    app_password = gmail_config.get("app_password", "")

    applied = results.get("applied", [])
    skipped = results.get("skipped", [])
    errors = results.get("errors", [])

    logger.info(
        f"Preparando email de resumen para {to_email} | "
        f"aplicadas={len(applied)} | externas={len(skipped)} | errores={len(errors)}"
    )

    if not sender or not app_password:
        logger.error("Credenciales Gmail incompletas — no se puede enviar el resumen")
        return

    subject = f"[Job Bot] Resumen semanal — {datetime.now().strftime('%d/%m/%Y')}"

    html = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #0077b5;">Resumen de aplicaciones — {user_name}</h2>
    <p style="color: #666;">Semana del {datetime.now().strftime('%d/%m/%Y')}</p>

    <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #2e7d32; margin: 0 0 10px 0;">Aplicaciones enviadas ({len(applied)})</h3>
        {"".join(f'''
        <div style="border-bottom: 1px solid #c8e6c9; padding: 8px 0;">
            <strong>{job['title']}</strong> — {job['company']}<br>
            <span style="color: #666; font-size: 0.9em;">Score: {job.get('match_score', 0)}% |
            <a href="{job['url']}">Ver oferta</a></span>
        </div>''' for job in applied) if applied else "<p>Ninguna esta semana</p>"}
    </div>

    <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #e65100; margin: 0 0 10px 0;">Links externos — aplicacion manual requerida ({len(skipped)})</h3>
        {"".join(f'''
        <div style="border-bottom: 1px solid #ffe0b2; padding: 8px 0;">
            <strong>{job['title']}</strong> — {job['company']}<br>
            <a href="{job['url']}" style="font-size: 0.9em;">Aplicar manualmente</a>
        </div>''' for job in skipped) if skipped else "<p>Ninguna</p>"}
    </div>

    {"" if not errors else f'''
    <div style="background: #fce4ec; padding: 15px; border-radius: 8px; margin: 15px 0;">
        <h3 style="color: #c62828; margin: 0 0 10px 0;">Errores ({len(errors)})</h3>
        {"".join(f"<p>{e}</p>" for e in errors)}
    </div>'''}

    <p style="color: #999; font-size: 0.8em; margin-top: 20px;">
        Proxima ejecucion: lunes siguiente a las 9:00 AM
    </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    try:
        logger.debug(f"Conectando a smtp.gmail.com:465 desde {sender}")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            logger.debug("Autenticacion SMTP exitosa")
            server.sendmail(sender, to_email, msg.as_string())
        logger.info(f"Email de resumen enviado exitosamente a {to_email}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(
            f"Error de autenticacion SMTP — verificar App Password de Gmail: {e}",
            exc_info=True
        )
    except smtplib.SMTPException as e:
        logger.error(f"Error SMTP enviando resumen a {to_email}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Error inesperado enviando email: {e}", exc_info=True)
