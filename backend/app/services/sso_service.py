"""
Servicio para interactuar con AWS IAM Identity Center.
Encapsula todas las llamadas a sso-admin e identitystore.

Arquitectura multi-cuenta:
- El backend corre con credenciales de la cuenta sandbox.
- Las llamadas a Identity Center (sso-admin, identitystore, organizations)
  se hacen asumiendo el role 'heimdall-identity-center-role' en la cuenta main.
- Si IDENTITY_CENTER_ROLE_ARN está vacío (desarrollo local con cuenta única)
  se usan las credenciales actuales directamente.
"""
import boto3
from functools import lru_cache
from app.config import settings


def _get_identity_center_credentials() -> dict:
    """
    Asume el role de Identity Center en la cuenta main y devuelve credenciales temporales.
    Si no hay role configurado, devuelve dict vacío (usa credenciales por defecto).
    """
    if not settings.IDENTITY_CENTER_ROLE_ARN:
        return {}

    sts = boto3.client("sts")
    assumed = sts.assume_role(
        RoleArn=settings.IDENTITY_CENTER_ROLE_ARN,
        RoleSessionName="heimdall-backend",
        DurationSeconds=3600,
    )
    creds = assumed["Credentials"]
    return {
        "aws_access_key_id":     creds["AccessKeyId"],
        "aws_secret_access_key": creds["SecretAccessKey"],
        "aws_session_token":     creds["SessionToken"],
    }


def get_sso_client():
    return boto3.client("sso-admin", region_name=settings.AWS_REGION, **_get_identity_center_credentials())


def get_identitystore_client():
    return boto3.client("identitystore", region_name=settings.AWS_REGION, **_get_identity_center_credentials())


def get_organizations_client():
    return boto3.client("organizations", region_name=settings.AWS_REGION, **_get_identity_center_credentials())


def get_identity_center_user_id(email: str) -> str:
    client = get_identitystore_client()
    response = client.get_user_id(
        IdentityStoreId=settings.IDENTITY_STORE_ID,
        AlternateIdentifier={
            "UniqueAttribute": {
                "AttributePath": "emails.value",
                "AttributeValue": email,
            }
        },
    )
    return response["UserId"]


@lru_cache(maxsize=1)
def get_admin_permission_set_arn() -> str | None:
    """
    Devuelve el ARN del permission set 'AdministratorAccess'.
    Resultado cacheado para no repetir llamadas a la API.
    """
    client = get_sso_client()
    paginator = client.get_paginator("list_permission_sets")
    for page in paginator.paginate(InstanceArn=settings.SSO_INSTANCE_ARN):
        for arn in page["PermissionSets"]:
            desc = client.describe_permission_set(
                InstanceArn=settings.SSO_INSTANCE_ARN,
                PermissionSetArn=arn,
            )
            if desc["PermissionSet"]["Name"] == "AdministratorAccess":
                return arn
    return None


def get_user_email_by_id(user_id: str) -> str | None:
    """Obtiene el email principal de un usuario de Identity Store por su ID."""
    client = get_identitystore_client()
    try:
        response = client.describe_user(
            IdentityStoreId=settings.IDENTITY_STORE_ID,
            UserId=user_id,
        )
        emails = response.get("Emails", [])
        for email in emails:
            if email.get("Primary"):
                return email["Value"]
        if emails:
            return emails[0]["Value"]
    except Exception:
        pass
    return None


def get_admin_emails_on_account(account_id: str) -> list[str]:
    """
    Devuelve los emails de todos los usuarios con AdministratorAccess
    en la cuenta indicada (asignaciones directas y por grupo).
    """
    try:
        admin_arn = get_admin_permission_set_arn()
        if not admin_arn:
            return []

        client = get_sso_client()
        idstore = get_identitystore_client()
        emails: set[str] = set()

        paginator = client.get_paginator("list_account_assignments")
        for page in paginator.paginate(
            InstanceArn=settings.SSO_INSTANCE_ARN,
            AccountId=account_id,
            PermissionSetArn=admin_arn,
        ):
            for assignment in page["AccountAssignments"]:
                if assignment["PrincipalType"] == "USER":
                    email = get_user_email_by_id(assignment["PrincipalId"])
                    if email:
                        emails.add(email)
                elif assignment["PrincipalType"] == "GROUP":
                    try:
                        mp = idstore.get_paginator("list_group_memberships")
                        for p in mp.paginate(
                            IdentityStoreId=settings.IDENTITY_STORE_ID,
                            GroupId=assignment["PrincipalId"],
                        ):
                            for member in p["GroupMemberships"]:
                                uid = member["MemberId"].get("UserId")
                                if uid:
                                    email = get_user_email_by_id(uid)
                                    if email:
                                        emails.add(email)
                    except Exception:
                        pass
        return list(emails)
    except Exception:
        return []


def has_admin_access_on_account(user_email: str, account_id: str) -> bool:
    """
    Devuelve True si el usuario tiene el permission set AdministratorAccess
    asignado directamente (o a través de un grupo) en la cuenta indicada.
    """
    try:
        admin_arn = get_admin_permission_set_arn()
        if not admin_arn:
            return False

        user_id = get_identity_center_user_id(user_email)
        client = get_sso_client()
        idstore = get_identitystore_client()

        paginator = client.get_paginator("list_account_assignments")
        for page in paginator.paginate(
            InstanceArn=settings.SSO_INSTANCE_ARN,
            AccountId=account_id,
            PermissionSetArn=admin_arn,
        ):
            for assignment in page["AccountAssignments"]:
                # Asignación directa al usuario
                if assignment["PrincipalType"] == "USER" and assignment["PrincipalId"] == user_id:
                    return True

                # Asignación a un grupo — comprobar si el usuario es miembro
                if assignment["PrincipalType"] == "GROUP":
                    members_paginator = idstore.get_paginator("list_group_memberships")
                    for mp in members_paginator.paginate(
                        IdentityStoreId=settings.IDENTITY_STORE_ID,
                        GroupId=assignment["PrincipalId"],
                    ):
                        for member in mp["GroupMemberships"]:
                            if member["MemberId"].get("UserId") == user_id:
                                return True
        return False

    except Exception:
        return False


def list_permission_sets() -> list[dict]:
    client = get_sso_client()
    arns = []
    paginator = client.get_paginator("list_permission_sets")
    for page in paginator.paginate(InstanceArn=settings.SSO_INSTANCE_ARN):
        arns.extend(page["PermissionSets"])
    permission_sets = []
    for arn in arns:
        response = client.describe_permission_set(
            InstanceArn=settings.SSO_INSTANCE_ARN,
            PermissionSetArn=arn,
        )
        ps = response["PermissionSet"]
        permission_sets.append({
            "arn": arn,
            "name": ps.get("Name"),
            "description": ps.get("Description", ""),
            "session_duration": ps.get("SessionDuration", "PT1H"),
        })
    return permission_sets


def list_accounts() -> list[dict]:
    client = get_organizations_client()
    accounts = []
    paginator = client.get_paginator("list_accounts")
    for page in paginator.paginate():
        for account in page["Accounts"]:
            if account["Status"] == "ACTIVE":
                accounts.append({
                    "id": account["Id"],
                    "name": account["Name"],
                    "email": account["Email"],
                })
    return accounts


def create_account_assignment(user_id, account_id, permission_set_arn):
    client = get_sso_client()
    response = client.create_account_assignment(
        InstanceArn=settings.SSO_INSTANCE_ARN,
        TargetId=account_id,
        TargetType="AWS_ACCOUNT",
        PermissionSetArn=permission_set_arn,
        PrincipalType="USER",
        PrincipalId=user_id,
    )
    return response["AccountAssignmentCreationStatus"]["RequestId"]


def delete_account_assignment(user_id, account_id, permission_set_arn):
    client = get_sso_client()
    response = client.delete_account_assignment(
        InstanceArn=settings.SSO_INSTANCE_ARN,
        TargetId=account_id,
        TargetType="AWS_ACCOUNT",
        PermissionSetArn=permission_set_arn,
        PrincipalType="USER",
        PrincipalId=user_id,
    )
    return response["AccountAssignmentDeletionStatus"]["RequestId"]
