import logging
import smtplib
from os import environ

from utils.time import utcnow


logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.notifications = []
        self.email_host = environ.get("SMTP_HOST")
        self.email_port = int(environ.get("SMTP_PORT", "587"))
        self.email_user = environ.get("SMTP_USER")
        self.email_password = environ.get("SMTP_PASSWORD")
        self.email_use_tls = environ.get("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes", "on"}

    def send_email(self, to, subject, body):
        if not self.email_host or not self.email_user or not self.email_password:
            raise ValueError("SMTP configuration is incomplete")

        server = smtplib.SMTP(self.email_host, self.email_port)
        try:
            if self.email_use_tls:
                server.starttls()
            server.login(self.email_user, self.email_password)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(self.email_user, to, message)
            logger.info("Email sent to %s", to)
            return True
        except smtplib.SMTPException:
            logger.exception("Error sending email to %s", to)
            raise
        finally:
            server.quit()

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\n"
            f"A task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append(
            {
                "type": "task_assigned",
                "user_id": user.id,
                "task_id": task.id,
                "timestamp": utcnow(),
            }
        )

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [notification for notification in self.notifications if notification["user_id"] == user_id]
