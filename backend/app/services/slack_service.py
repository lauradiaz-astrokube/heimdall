"""
Servicio de notificaciones Slack para HeimdALL.
Envía DMs a los usuarios usando la Slack Web API.

Mapeo de emails: @astrokube.onmicrosoft.com → @astrokube.com
"""
import httpx
from app.config import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_email(email: str) -> str:
    """Convierte el email de Entra ID al email real de Slack."""
    if not email:
        return email
    return email.lower().replace(
        settings.ENTRA_EMAIL_DOMAIN.lower(),
        settings.SLACK_EMAIL_DOMAIN.lower(),
    )


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"}


def _get_user_id(email: str) -> str | None:
    """Busca el Slack user ID por email."""
    normalized = normalize_email(email)
    try:
        r = httpx.get(
            "https://slack.com/api/users.lookupByEmail",
            headers=_headers(),
            params={"email": normalized},
            timeout=10,
        )
        data = r.json()
        if data.get("ok"):
            return data["user"]["id"]
    except Exception:
        pass
    return None


def send_dm(email: str, text: str, blocks: list | None = None) -> bool:
    """
    Envía un DM a un usuario por su email de Entra ID.
    Devuelve True si el mensaje se envió correctamente.
    Si SLACK_BOT_TOKEN no está configurado, no hace nada.
    """
    if not settings.SLACK_BOT_TOKEN:
        return False

    user_id = _get_user_id(email)
    if not user_id:
        print(f"[Slack] Usuario no encontrado: {normalize_email(email)}")
        return False

    try:
        # Abrir canal DM
        open_r = httpx.post(
            "https://slack.com/api/conversations.open",
            headers=_headers(),
            json={"users": user_id},
            timeout=10,
        )
        channel_id = open_r.json().get("channel", {}).get("id")
        if not channel_id:
            return False

        # Enviar mensaje
        payload: dict = {"channel": channel_id, "text": text}
        if blocks:
            payload["blocks"] = blocks

        httpx.post(
            "https://slack.com/api/chat.postMessage",
            headers=_headers(),
            json=payload,
            timeout=10,
        )
        return True
    except Exception as e:
        print(f"[Slack] Error enviando DM a {email}: {e}")
        return False


# ---------------------------------------------------------------------------
# Mensajes
# ---------------------------------------------------------------------------

def notify_request_created(
    admin_email: str,
    requestor_email: str,
    account_name: str,
    permission_set_name: str,
    duration_hours: int,
    justification: str,
    app_url: str = "https://lauradiaz-astrokube.github.io/heimdall/",
):
    """Notifica a un administrador que hay una nueva solicitud de acceso."""
    text = f"Nueva solicitud de acceso de {normalize_email(requestor_email)}"
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Nueva solicitud de acceso"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Solicitante:*\n{normalize_email(requestor_email)}"},
                {"type": "mrkdwn", "text": f"*Cuenta AWS:*\n{account_name}"},
                {"type": "mrkdwn", "text": f"*Nivel de acceso:*\n{permission_set_name}"},
                {"type": "mrkdwn", "text": f"*Duración:*\n{duration_hours}h"},
            ]
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Justificación:*\n>{justification}"}
        },
        {
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "Revisar solicitudes"},
                "url": f"{app_url}approvals",
                "style": "primary",
            }]
        }
    ]
    send_dm(admin_email, text, blocks)


def notify_request_approved(
    requestor_email: str,
    account_name: str,
    permission_set_name: str,
    expires_at_iso: str,
    app_url: str = "https://lauradiaz-astrokube.github.io/heimdall/",
):
    """Notifica al solicitante que su acceso ha sido aprobado."""
    text = f"Tu solicitud de acceso a {account_name} ha sido aprobada"
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Acceso aprobado"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Cuenta AWS:*\n{account_name}"},
                {"type": "mrkdwn", "text": f"*Nivel de acceso:*\n{permission_set_name}"},
                {"type": "mrkdwn", "text": f"*Expira el:*\n{expires_at_iso}"},
            ]
        },
        {
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "Ver mis accesos"},
                "url": app_url,
            }]
        }
    ]
    send_dm(requestor_email, text, blocks)


def notify_request_rejected(
    requestor_email: str,
    account_name: str,
    permission_set_name: str,
    comment: str,
):
    """Notifica al solicitante que su solicitud ha sido rechazada."""
    text = f"Tu solicitud de acceso a {account_name} ha sido rechazada"
    fields = [
        {"type": "mrkdwn", "text": f"*Cuenta AWS:*\n{account_name}"},
        {"type": "mrkdwn", "text": f"*Nivel de acceso:*\n{permission_set_name}"},
    ]
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Solicitud rechazada"}
        },
        {"type": "section", "fields": fields},
    ]
    if comment:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Motivo:*\n>{comment}"}
        })
    send_dm(requestor_email, text, blocks)


def notify_access_revoked(
    requestor_email: str,
    account_name: str,
    permission_set_name: str,
    reason: str = "expiración automática",
):
    """Notifica al usuario que su acceso ha sido revocado."""
    text = f"Tu acceso a {account_name} ha sido revocado"
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Acceso revocado"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Cuenta AWS:*\n{account_name}"},
                {"type": "mrkdwn", "text": f"*Nivel de acceso:*\n{permission_set_name}"},
                {"type": "mrkdwn", "text": f"*Motivo:*\n{reason}"},
            ]
        }
    ]
    send_dm(requestor_email, text, blocks)
