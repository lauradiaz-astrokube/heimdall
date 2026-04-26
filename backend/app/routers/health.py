from fastapi import APIRouter, Depends
from app.auth.jwt_validator import get_current_user

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/public")
def health_public():
    """Endpoint público para verificar que el servicio está activo (sin auth)."""
    return {"status": "ok"}


@router.get("/private")
def health_private(user: dict = Depends(get_current_user)):
    """
    Endpoint protegido para verificar que la autenticación funciona.
    Si devuelve 200, el token JWT de Identity Center es válido.
    """
    return {
        "status": "ok",
        "authenticated_as": user["email"],
        "user_id": user["sub"],
    }
