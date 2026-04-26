import json
import boto3
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.auth.jwt_validator import get_current_user
from app.services import dynamodb_service
from app.services import sso_service
from app.config import settings

router = APIRouter(prefix="/requests", tags=["requests"])


class CreateRequestBody(BaseModel):
    account_id: str
    account_name: str
    permission_set_arn: str
    permission_set_name: str
    justification: str = Field(min_length=10)
    duration_hours: int = Field(ge=1, le=24)


class ApprovalBody(BaseModel):
    comment: str = ""


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_request(
    body: CreateRequestBody,
    user: dict = Depends(get_current_user),
):
    """
    Crea una nueva solicitud de acceso temporal.
    La solicitud queda en estado PENDING hasta que un aprobador la valide.
    """
    request = dynamodb_service.create_request(
        requestor_id=user["sub"],
        requestor_email=user["email"],
        account_id=body.account_id,
        account_name=body.account_name,
        permission_set_arn=body.permission_set_arn,
        permission_set_name=body.permission_set_name,
        justification=body.justification,
        duration_hours=body.duration_hours,
    )

    dynamodb_service.log_event(
        entity="AccessRequest",
        action="CREATED",
        actor_email=user["email"],
        payload={
            "request_id": request["id"],
            "account_id": body.account_id,
            "permission_set": body.permission_set_name,
        },
    )

    return request


@router.get("/my")
def get_my_requests(user: dict = Depends(get_current_user)):
    """Devuelve todas las solicitudes del usuario autenticado."""
    return dynamodb_service.get_requests_by_user(user["sub"])


@router.get("/pending")
def get_pending_requests(user: dict = Depends(get_current_user)):
    """
    Devuelve todas las solicitudes pendientes de aprobación.
    Solo accesible por aprobadores (en el MVP cualquier usuario autenticado puede ver).
    """
    return dynamodb_service.get_pending_requests()


@router.post("/{request_id}/approve")
def approve_request(
    request_id: str,
    body: ApprovalBody,
    user: dict = Depends(get_current_user),
):
    """
    Aprueba una solicitud de acceso:
    1. Actualiza el estado a APPROVED en DynamoDB
    2. Llama a sso-admin:CreateAccountAssignment para conceder el acceso
    3. Registra el grant activo con su fecha de expiración
    4. Registra el evento en auditoría
    """
    # Obtener la solicitud
    pending = dynamodb_service.get_pending_requests()
    request = next((r for r in pending if r["id"] == request_id), None)

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada o ya procesada",
        )

    # Evitar que el solicitante se apruebe a sí mismo
    #if request["requestor_id"] == user["sub"]:
        #raise HTTPException(
            #status_code=status.HTTP_403_FORBIDDEN,
            #detail="No puedes aprobar tu propia solicitud",
        #)

    # Verificar que el aprobador tiene AdministratorAccess en la cuenta solicitada
    if not sso_service.has_admin_access_on_account(user["email"], request["account_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores de la cuenta pueden aprobar esta solicitud",
        )

    # 1. Actualizar estado en DynamoDB
    dynamodb_service.update_request_status(
        request_id=request_id,
        status="APPROVED",
        approver_email=user["email"],
        comment=body.comment,
    )

    # 2. Conceder acceso en Identity Center
    # El requestor_id es el sub de Entra ID, no el ID de Identity Center.
    # Hay que traducirlo buscando por email.
    identity_center_user_id = sso_service.get_identity_center_user_id(
        request["requestor_email"]
    )
    sso_service.create_account_assignment(
        user_id=identity_center_user_id,
        account_id=request["account_id"],
        permission_set_arn=request["permission_set_arn"],
    )

    # 3. Registrar grant con TTL de expiración
    expires_at = datetime.now(timezone.utc) + timedelta(hours=int(request["duration_hours"]))
    grant = dynamodb_service.create_grant(
        request_id=request_id,
        requestor_id=request["requestor_id"],
        account_id=request["account_id"],
        account_name=request.get("account_name", request["account_id"]),
        permission_set_arn=request["permission_set_arn"],
        permission_set_name=request.get("permission_set_name", request["permission_set_arn"]),
        expires_at_timestamp=int(expires_at.timestamp()),
    )

    # 4. Programar revocación automática con EventBridge Scheduler
    _schedule_revocation(
        grant_id=grant["id"],
        requestor_email=request["requestor_email"],
        account_id=request["account_id"],
        permission_set_arn=request["permission_set_arn"],
        expires_at=expires_at,
    )

    # 5. Auditoría
    dynamodb_service.log_event(
        entity="AccessRequest",
        action="APPROVED",
        actor_email=user["email"],
        payload={
            "request_id": request_id,
            "requestor_email": request["requestor_email"],
            "expires_at": expires_at.isoformat(),
        },
    )

    return {"status": "approved", "expires_at": expires_at.isoformat()}


def _schedule_revocation(
    grant_id: str,
    requestor_email: str,
    account_id: str,
    permission_set_arn: str,
    expires_at: datetime,
):
    """
    Crea un schedule de un solo uso en EventBridge Scheduler
    para revocar el acceso cuando caduque el grant.
    Si los ARNs no están configurados (entorno local), omite el paso.
    """
    if not settings.REVOKE_LAMBDA_ARN or not settings.SCHEDULER_ROLE_ARN:
        print("REVOKE_LAMBDA_ARN o SCHEDULER_ROLE_ARN no configurados — omitiendo schedule")
        return

    scheduler = boto3.client("scheduler", region_name=settings.AWS_REGION)

    # Formato requerido por EventBridge: yyyy-MM-ddTHH:mm:ss (sin zona horaria)
    schedule_time = expires_at.strftime("%Y-%m-%dT%H:%M:%S")

    scheduler.create_schedule(
        Name=f"revoke-{grant_id}",
        ScheduleExpression=f"at({schedule_time})",
        ScheduleExpressionTimezone="UTC",
        Target={
            "Arn": settings.REVOKE_LAMBDA_ARN,
            "RoleArn": settings.SCHEDULER_ROLE_ARN,
            "Input": json.dumps({
                "grant_id": grant_id,
                "requestor_email": requestor_email,
                "account_id": account_id,
                "permission_set_arn": permission_set_arn,
            }),
        },
        FlexibleTimeWindow={"Mode": "OFF"},
        ActionAfterCompletion="DELETE",  # Borra el schedule tras ejecutarse
    )


@router.post("/{request_id}/reject")
def reject_request(
    request_id: str,
    body: ApprovalBody,
    user: dict = Depends(get_current_user),
):
    """
    Rechaza una solicitud de acceso.
    """
    pending = dynamodb_service.get_pending_requests()
    request = next((r for r in pending if r["id"] == request_id), None)

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada o ya procesada",
        )

    if request["requestor_id"] == user["sub"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes rechazar tu propia solicitud",
        )

    dynamodb_service.update_request_status(
        request_id=request_id,
        status="REJECTED",
        approver_email=user["email"],
        comment=body.comment,
    )

    dynamodb_service.log_event(
        entity="AccessRequest",
        action="REJECTED",
        actor_email=user["email"],
        payload={
            "request_id": request_id,
            "requestor_email": request["requestor_email"],
            "comment": body.comment,
        },
    )

    return {"status": "rejected"}
