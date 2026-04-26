"""
Lambda de revocación automática de HeimdALL.

EventBridge Scheduler llama a esta función cuando caduca un grant.
Revoca el acceso en Identity Center y actualiza el estado en DynamoDB.

Evento de entrada esperado:
{
    "grant_id": "uuid",
    "requestor_email": "user@empresa.com",
    "account_id": "123456789012",
    "permission_set_arn": "arn:aws:sso:::permissionSet/..."
}
"""
import json
import uuid
import boto3
import os
from datetime import datetime, timezone


SSO_INSTANCE_ARN = os.environ["SSO_INSTANCE_ARN"]
IDENTITY_STORE_ID = os.environ["IDENTITY_STORE_ID"]
DYNAMODB_TABLE_PREFIX = os.environ.get("DYNAMODB_TABLE_PREFIX", "heimdall")
IDENTITY_CENTER_ROLE_ARN = os.environ.get("IDENTITY_CENTER_ROLE_ARN", "")

# AWS_REGION es reservada en Lambda — se obtiene de boto3
import boto3 as _boto3
AWS_REGION = _boto3.session.Session().region_name or "eu-west-1"


def _get_identity_center_credentials() -> dict:
    """Asume el role de Identity Center en la cuenta main si está configurado."""
    if not IDENTITY_CENTER_ROLE_ARN:
        return {}
    sts = boto3.client("sts")
    assumed = sts.assume_role(
        RoleArn=IDENTITY_CENTER_ROLE_ARN,
        RoleSessionName="heimdall-revoke-lambda",
        DurationSeconds=900,
    )
    creds = assumed["Credentials"]
    return {
        "aws_access_key_id":     creds["AccessKeyId"],
        "aws_secret_access_key": creds["SecretAccessKey"],
        "aws_session_token":     creds["SessionToken"],
    }


def get_identity_center_user_id(email: str) -> str:
    client = boto3.client("identitystore", region_name=AWS_REGION, **_get_identity_center_credentials())
    response = client.get_user_id(
        IdentityStoreId=IDENTITY_STORE_ID,
        AlternateIdentifier={
            "UniqueAttribute": {
                "AttributePath": "emails.value",
                "AttributeValue": email,
            }
        },
    )
    return response["UserId"]


def revoke_access(user_id: str, account_id: str, permission_set_arn: str):
    client = boto3.client("sso-admin", region_name=AWS_REGION, **_get_identity_center_credentials())
    response = client.delete_account_assignment(
        InstanceArn=SSO_INSTANCE_ARN,
        TargetId=account_id,
        TargetType="AWS_ACCOUNT",
        PermissionSetArn=permission_set_arn,
        PrincipalType="USER",
        PrincipalId=user_id,
    )
    return response["AccountAssignmentDeletionStatus"]["RequestId"]


def update_grant_status(grant_id: str):
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-dev-grants")
    table.update_item(
        Key={"id": grant_id},
        UpdateExpression="SET #s = :status, revoked_at = :ts",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":status": "REVOKED",
            ":ts": datetime.now(timezone.utc).isoformat(),
        },
    )


def log_audit_event(grant_id: str, email: str):
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(f"{DYNAMODB_TABLE_PREFIX}-dev-audit")
    table.put_item(Item={
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entity": "ActiveGrant",
        "action": "AUTO_REVOKED",
        "actor_email": "system",
        "payload": {
            "grant_id": grant_id,
            "requestor_email": email,
        },
    })


def lambda_handler(event, context):
    print(f"Revocando grant: {json.dumps(event)}")

    grant_id = event["grant_id"]
    requestor_email = event["requestor_email"]
    account_id = event["account_id"]
    permission_set_arn = event["permission_set_arn"]

    # 1. Obtener el ID de Identity Center del usuario
    identity_center_user_id = get_identity_center_user_id(requestor_email)

    # 2. Revocar acceso en Identity Center
    revoke_access(identity_center_user_id, account_id, permission_set_arn)

    # 3. Actualizar estado del grant en DynamoDB
    update_grant_status(grant_id)

    # 4. Registrar en auditoría
    log_audit_event(grant_id, requestor_email)

    # 5. Notificar al usuario por Slack
    slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
    slack_email_domain = os.environ.get("SLACK_EMAIL_DOMAIN", "astrokube.com")
    entra_domain = os.environ.get("ENTRA_EMAIL_DOMAIN", "astrokube.onmicrosoft.com")
    account_name = event.get("account_name", account_id)
    permission_set_name = event.get("permission_set_name", permission_set_arn)

    if slack_token:
        _send_slack_revoke_dm(
            token=slack_token,
            email=requestor_email,
            account_name=account_name,
            permission_set_name=permission_set_name,
            entra_domain=entra_domain,
            slack_domain=slack_email_domain,
        )

    print(f"Grant {grant_id} revocado correctamente")
    return {"status": "revoked", "grant_id": grant_id}


def _send_slack_revoke_dm(token, email, account_name, permission_set_name, entra_domain, slack_domain):
    """Envía un DM de Slack cuando se revoca un acceso automáticamente."""
    import urllib.request
    normalized = email.lower().replace(entra_domain.lower(), slack_domain.lower())

    def slack_post(url, data):
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    def slack_get(url, params):
        query = "&".join(f"{k}={v}" for k, v in params.items())
        req = urllib.request.Request(
            f"{url}?{query}",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())

    try:
        user_resp = slack_get("https://slack.com/api/users.lookupByEmail", {"email": normalized})
        if not user_resp.get("ok"):
            return
        user_id = user_resp["user"]["id"]

        ch_resp = slack_post("https://slack.com/api/conversations.open", {"users": user_id})
        channel_id = ch_resp.get("channel", {}).get("id")
        if not channel_id:
            return

        slack_post("https://slack.com/api/chat.postMessage", {
            "channel": channel_id,
            "text": f"Tu acceso a {account_name} ha expirado y ha sido revocado automáticamente.",
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": "Acceso revocado automáticamente"}},
                {"type": "section", "fields": [
                    {"type": "mrkdwn", "text": f"*Cuenta AWS:*\n{account_name}"},
                    {"type": "mrkdwn", "text": f"*Nivel de acceso:*\n{permission_set_name}"},
                    {"type": "mrkdwn", "text": "*Motivo:*\nExpiración del tiempo solicitado"},
                ]},
            ]
        })
    except Exception as e:
        print(f"[Slack] Error en revoke_handler: {e}")
