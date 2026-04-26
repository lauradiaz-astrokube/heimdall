from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ------------------------------------------------------------------
    # Microsoft Entra ID / OIDC
    # ------------------------------------------------------------------
    # Tenant ID de la organización en Entra ID
    # Entra ID → Overview → Tenant ID
    ENTRA_TENANT_ID: str

    # Client ID de HeimdALL registrada en Entra ID
    # Entra ID → App registrations → HeimdALL → Application (client) ID
    OIDC_CLIENT_ID: str

    # ------------------------------------------------------------------
    # AWS general
    # ------------------------------------------------------------------
    AWS_REGION: str = "eu-west-1"

    # ARN de la instancia de Identity Center
    # Ejemplo: arn:aws:sso:::instance/ssoins-xxxxxxxxxxxxxxxx
    SSO_INSTANCE_ARN: str
    IDENTITY_STORE_ID: str

    # ARN del role en la cuenta main para llamar a Identity Center
    # (arquitectura multi-cuenta: backend en sandbox, Identity Center en main)
    IDENTITY_CENTER_ROLE_ARN: str = ""

    # ------------------------------------------------------------------
    # Revocación automática (EventBridge Scheduler + Lambda)
    # ------------------------------------------------------------------
    # ARN de la Lambda de revocación
    REVOKE_LAMBDA_ARN: str = ""

    # ARN del rol IAM que EventBridge usa para invocar la Lambda
    SCHEDULER_ROLE_ARN: str = ""

    # ------------------------------------------------------------------
    # Slack
    # ------------------------------------------------------------------
    # Bot User OAuth Token de la Slack App de HeimdALL (xoxb-...)
    SLACK_BOT_TOKEN: str = ""

    # Dominio real de Slack (@astrokube.com) para mapear desde onmicrosoft.com
    SLACK_EMAIL_DOMAIN: str = "astrokube.com"
    ENTRA_EMAIL_DOMAIN: str = "astrokube.onmicrosoft.com"

    # ------------------------------------------------------------------
    # DynamoDB
    # ------------------------------------------------------------------
    # Prefijo para las tablas (permite múltiples entornos en la misma cuenta)
    DYNAMODB_TABLE_PREFIX: str = "heimdall"

    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------
    # Orígenes permitidos para CORS (frontend)
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
