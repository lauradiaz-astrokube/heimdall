import boto3
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.jwt_validator import get_current_user
from app.services import dynamodb_service, sso_service, slack_service
from app.config import settings

router = APIRouter(prefix="/grants", tags=["grants"])


@router.get("/my")
def get_my_active_grants(user: dict = Depends(get_current_user)):
    """Devuelve los grants activos del usuario autenticado."""
    return dynamodb_service.get_active_grants_by_user(user["sub"])


@router.post("/{grant_id}/revoke", status_code=status.HTTP_200_OK)
def revoke_grant(grant_id: str, user: dict = Depends(get_current_user)):
    """
    Revocación de emergencia de un grant activo.
    1. Verifica que el grant pertenece al usuario o que es aprobador
    2. Revoca el acceso en Identity Center
    3. Cancela el schedule de EventBridge si existe
    4. Actualiza el estado del grant a REVOKED
    5. Registra el evento en auditoría
    """
    # Buscar el grant (en todos los activos, no solo los del usuario)
    all_grants = dynamodb_service.get_all_active_grants()
    grant = next((g for g in all_grants if g["id"] == grant_id), None)

    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant no encontrado o ya revocado",
        )

    # Verificar autorización: debe ser el propietario del grant O tener AdministratorAccess en la cuenta
    is_owner = grant["requestor_id"] == user["sub"]
    is_admin = sso_service.has_admin_access_on_account(user["email"], grant["account_id"])

    if not is_owner and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el propietario del acceso o un administrador de la cuenta pueden revocarlo",
        )

    # 1. Obtener el user ID de Identity Center
    identity_center_user_id = sso_service.get_identity_center_user_id(user["email"])

    # 2. Revocar en Identity Center
    sso_service.delete_account_assignment(
        user_id=identity_center_user_id,
        account_id=grant["account_id"],
        permission_set_arn=grant["permission_set_arn"],
    )

    # 3. Cancelar el schedule de EventBridge si existe
    _cancel_schedule(grant_id)

    # 4. Actualizar estado del grant
    dynamodb_service.update_grant_status(
        grant_id=grant_id,
        status="REVOKED",
        revoked_by=user["email"],
    )

    # 5. Auditoría
    dynamodb_service.log_event(
        entity="ActiveGrant",
        action="MANUALLY_REVOKED",
        actor_email=user["email"],
        payload={
            "grant_id": grant_id,
            "account_id": grant["account_id"],
            "permission_set_arn": grant["permission_set_arn"],
        },
    )

    # Notificar al propietario del grant
    requestor_email = grant.get("requestor_email") or grant.get("requestor_id", "")
    if requestor_email:
        slack_service.notify_access_revoked(
            requestor_email=requestor_email,
            account_name=grant.get("account_name", grant["account_id"]),
            permission_set_name=grant.get("permission_set_name", grant["permission_set_arn"]),
            reason="revocación manual",
        )

    return {"status": "revoked", "grant_id": grant_id}


def _cancel_schedule(grant_id: str):
    """Elimina el schedule de EventBridge si existe. Ignora el error si ya no existe."""
    if not settings.SCHEDULER_ROLE_ARN:
        return
    try:
        scheduler = boto3.client("scheduler", region_name=settings.AWS_REGION)
        scheduler.delete_schedule(Name=f"revoke-{grant_id}")
    except scheduler.exceptions.ResourceNotFoundException:
        pass  # Ya fue ejecutado o no existía
    except Exception:
        pass  # No bloquear la revocación si falla el scheduler
