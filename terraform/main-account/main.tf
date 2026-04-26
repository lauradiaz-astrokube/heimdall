terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.6"
}

# Credenciales de la cuenta MAIN (la que tiene Identity Center)
# Configura el perfil en ~/.aws/credentials como [main]
provider "aws" {
  region  = "eu-west-1"
  profile = "default"
}

variable "sandbox_account_id" {
  type        = string
  description = "ID de la cuenta sandbox que asumirá este role"
  default     = "767397738908"
}

# ---------------------------------------------------------------------------
# Role en la cuenta MAIN que la sandbox puede asumir para llamar a
# IAM Identity Center (sso-admin, identitystore, organizations)
# ---------------------------------------------------------------------------

resource "aws_iam_role" "heimdall_identity_center_role" {
  name = "heimdall-identity-center-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { AWS = "arn:aws:iam::${var.sandbox_account_id}:root" }
      Action    = "sts:AssumeRole"
    }]
  })

  description = "Role para que el backend de HeimdALL (sandbox) acceda a Identity Center"
}

resource "aws_iam_role_policy" "heimdall_identity_center_policy" {
  name = "heimdall-identity-center-policy"
  role = aws_iam_role.heimdall_identity_center_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        # SSO Admin API (prefijo sso-admin)
        "sso-admin:ListPermissionSets",
        "sso-admin:DescribePermissionSet",
        "sso-admin:ListAccountAssignments",
        "sso-admin:CreateAccountAssignment",
        "sso-admin:DeleteAccountAssignment",
        # SSO API (prefijo sso — usado internamente por algunas operaciones)
        "sso:ListPermissionSets",
        "sso:DescribePermissionSet",
        "sso:ListAccountAssignments",
        "sso:CreateAccountAssignment",
        "sso:DeleteAccountAssignment",
        # Identity Store — buscar usuarios y grupos
        "identitystore:GetUserId",
        "identitystore:ListGroupMemberships",
        # Organizations — listar cuentas para el catálogo
        "organizations:ListAccounts",
      ]
      Resource = "*"
    }]
  })
}

output "identity_center_role_arn" {
  value       = aws_iam_role.heimdall_identity_center_role.arn
  description = "ARN del role — añadir a IDENTITY_CENTER_ROLE_ARN en .env del backend"
}
