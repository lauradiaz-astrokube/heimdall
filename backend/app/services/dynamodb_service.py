"""
Servicio para interactuar con DynamoDB.
Encapsula todas las operaciones CRUD sobre las tablas de HeimdALL.
"""
import uuid
import boto3
from datetime import datetime, timezone
from app.config import settings


def get_table(name: str):
    dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
    return dynamodb.Table(f"{settings.DYNAMODB_TABLE_PREFIX}-dev-{name}")


# ---------------------------------------------------------------------------
# Solicitudes (requests)
# ---------------------------------------------------------------------------

def create_request(
    requestor_id: str,
    requestor_email: str,
    account_id: str,
    account_name: str,
    permission_set_arn: str,
    permission_set_name: str,
    justification: str,
    duration_hours: int,
) -> dict:
    """Crea una nueva solicitud de acceso con estado PENDING."""
    table = get_table("requests")

    request = {
        "id": str(uuid.uuid4()),
        "requestor_id": requestor_id,
        "requestor_email": requestor_email,
        "account_id": account_id,
        "account_name": account_name,
        "permission_set_arn": permission_set_arn,
        "permission_set_name": permission_set_name,
        "justification": justification,
        "duration_hours": duration_hours,
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    table.put_item(Item=request)
    return request


def get_requests_by_user(requestor_id: str) -> list[dict]:
    """Devuelve todas las solicitudes de un usuario."""
    table = get_table("requests")
    response = table.query(
        IndexName="by-requestor",
        KeyConditionExpression="requestor_id = :uid",
        ExpressionAttributeValues={":uid": requestor_id},
    )
    return response.get("Items", [])


def get_pending_requests() -> list[dict]:
    """Devuelve todas las solicitudes pendientes de aprobación."""
    table = get_table("requests")
    response = table.query(
        IndexName="by-status",
        KeyConditionExpression="#s = :status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": "PENDING"},
    )
    return response.get("Items", [])


def update_request_status(
    request_id: str,
    status: str,
    approver_email: str = None,
    comment: str = None,
) -> None:
    """Actualiza el estado de una solicitud (APPROVED, REJECTED)."""
    table = get_table("requests")

    update_expr = "SET #s = :status, updated_at = :ts"
    expr_names = {"#s": "status"}
    expr_values = {
        ":status": status,
        ":ts": datetime.now(timezone.utc).isoformat(),
    }

    if approver_email:
        update_expr += ", approver_email = :approver"
        expr_values[":approver"] = approver_email

    if comment:
        update_expr += ", approver_comment = :comment"
        expr_values[":comment"] = comment

    table.update_item(
        Key={"id": request_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )


# ---------------------------------------------------------------------------
# Grants activos
# ---------------------------------------------------------------------------

def create_grant(
    request_id: str,
    requestor_id: str,
    account_id: str,
    account_name: str,
    permission_set_arn: str,
    permission_set_name: str,
    expires_at_timestamp: int,
) -> dict:
    """Registra un grant activo. expires_at es un Unix timestamp para el TTL."""
    table = get_table("grants")

    grant = {
        "id": str(uuid.uuid4()),
        "request_id": request_id,
        "requestor_id": requestor_id,
        "account_id": account_id,
        "account_name": account_name,
        "permission_set_arn": permission_set_arn,
        "permission_set_name": permission_set_name,
        "status": "ACTIVE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at_timestamp,  # TTL de DynamoDB (Unix timestamp)
        "expires_at_iso": datetime.fromtimestamp(expires_at_timestamp, tz=timezone.utc).isoformat(),
    }

    table.put_item(Item=grant)
    return grant


def update_grant_status(grant_id: str, status: str, revoked_by: str = None) -> None:
    """Actualiza el estado de un grant (REVOKED)."""
    table = get_table("grants")
    update_expr = "SET #s = :status, revoked_at = :ts"
    expr_names = {"#s": "status"}
    expr_values = {
        ":status": status,
        ":ts": datetime.now(timezone.utc).isoformat(),
    }
    if revoked_by:
        update_expr += ", revoked_by = :by"
        expr_values[":by"] = revoked_by
    table.update_item(
        Key={"id": grant_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
    )


def get_all_active_grants() -> list[dict]:
    """Devuelve todos los grants activos (para administradores)."""
    table = get_table("grants")
    response = table.scan(
        FilterExpression="#s = :active",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":active": "ACTIVE"},
    )
    return response.get("Items", [])


def get_active_grants_by_user(requestor_id: str) -> list[dict]:
    """Devuelve los grants activos de un usuario (scan con filtro)."""
    table = get_table("grants")
    response = table.scan(
        FilterExpression="#s = :active AND requestor_id = :uid",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":active": "ACTIVE", ":uid": requestor_id},
    )
    return response.get("Items", [])


# ---------------------------------------------------------------------------
# Auditoría
# ---------------------------------------------------------------------------

def log_event(
    entity: str,
    action: str,
    actor_email: str,
    payload: dict = None,
) -> None:
    """Registra un evento en el log de auditoría."""
    table = get_table("audit")

    table.put_item(Item={
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entity": entity,
        "action": action,
        "actor_email": actor_email,
        "payload": payload or {},
    })
