from fastapi import APIRouter, Depends
from app.auth.jwt_validator import get_current_user
from app.services import sso_service

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/permission-sets")
def get_permission_sets(user: dict = Depends(get_current_user)):
    """
    Lista los permission sets disponibles para solicitar.
    El usuario autenticado puede ver todos los permission sets
    configurados en Identity Center.
    """
    return sso_service.list_permission_sets()


@router.get("/accounts")
def get_accounts(user: dict = Depends(get_current_user)):
    """
    Lista las cuentas AWS de la organización a las que se puede
    solicitar acceso temporal.
    """
    return sso_service.list_accounts()
