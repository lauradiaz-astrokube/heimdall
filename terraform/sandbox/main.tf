terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.6"
}

# Credenciales de la cuenta SANDBOX
# Configura el perfil en ~/.aws/credentials como [sandbox]
provider "aws" {
  region  = "eu-west-1"
  profile = "sandbox"
}

variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "sso_instance_arn" {
  type        = string
  description = "ARN de la instancia de IAM Identity Center (cuenta main)"
}

variable "identity_store_id" {
  type        = string
  description = "ID del Identity Store (cuenta main)"
}

variable "main_account_id" {
  type        = string
  description = "ID de la cuenta main donde está Identity Center"
  default     = "921780870478"
}

variable "entra_tenant_id" {
  type        = string
  description = "Tenant ID de Microsoft Entra ID"
}

variable "oidc_client_id" {
  type        = string
  description = "Client ID de HeimdALL en Entra ID"
}

variable "slack_bot_token" {
  type        = string
  description = "Bot User OAuth Token de la Slack App de HeimdALL (xoxb-...)"
  default     = ""
  sensitive   = true
}
