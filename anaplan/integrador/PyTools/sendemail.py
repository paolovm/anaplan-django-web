"""Notificações de status de carga via o backend de e-mail do Django.

Host, porta, credenciais, remetente e destinatários vêm das settings/ambiente
(EMAIL_*, DEFAULT_FROM_EMAIL, ANAPLAN_NOTIFY_RECIPIENTS). Nenhum segredo no código.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def sendEmail(subject="Anaplan Status", status="Status não especificado"):
    recipients = settings.ANAPLAN_NOTIFY_RECIPIENTS
    if not recipients or not settings.EMAIL_HOST:
        logger.info("Notificação por e-mail ignorada (sem destinatários ou EMAIL_HOST configurado).")
        return

    try:
        send_mail(subject, status, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=False)
        logger.info("E-mail de notificação enviado: %s", subject)
    except Exception:
        logger.exception("Falha ao enviar e-mail de notificação")
