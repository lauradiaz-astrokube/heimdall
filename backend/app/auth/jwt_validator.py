"""
Validación de tokens JWT emitidos por Microsoft Entra ID.

El frontend autentica al usuario contra Entra ID (OIDC/PKCE).
Entra ID emite tokens JWT firmados con RS256.
El backend descarga las claves públicas JWKS de Entra ID y valida
cada token entrante sin necesidad de llamar a ningún servicio externo
en cada request (las claves se cachean en memoria).

Identity Center confía en estos tokens via el trusted token issuer configurado.
"""
import httpx
from functools import lru_cache
from jose import jwt, JWTError
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

security_scheme = HTTPBearer()


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """
    Descarga las claves públicas JWKS de Entra ID.
    Se cachean en memoria (lru_cache) para no hacer una petición HTTP
    en cada validación de token.

    Endpoint: https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys
    """
    jwks_uri = (
        f"https://login.microsoftonline.com/"
        f"{settings.ENTRA_TENANT_ID}/discovery/v2.0/keys"
    )
    response = httpx.get(jwks_uri, timeout=10)
    response.raise_for_status()
    return response.json()


def validate_token(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
) -> dict:
    """
    Dependencia de FastAPI que valida el Bearer token en cada request protegida.

    Comprueba:
    - Firma válida con las claves JWKS de Entra ID
    - Token no expirado
    - Issuer correcto (Entra ID del tenant de la organización)
    - Audience correcta (client_id de HeimdALL en Entra ID)

    Devuelve el payload decodificado del JWT (claims del usuario).
    """
    token = credentials.credentials

    try:
        jwks = _get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.OIDC_CLIENT_ID,
            issuer=f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}/v2.0",
        )
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(payload: dict = Security(validate_token)) -> dict:
    """
    Extrae los datos del usuario autenticado del payload JWT de Entra ID.
    Úsala como dependencia en los endpoints que necesiten saber quién llama.

    Ejemplo:
        @router.get("/me")
        def get_me(user = Depends(get_current_user)):
            return user
    """
    return {
        "sub": payload.get("sub"),            # ID único del usuario en Entra ID
        "email": payload.get("email") or payload.get("preferred_username"),
        "name": payload.get("name"),
        "groups": payload.get("groups", []),  # IDs de grupos de Entra ID
    }
