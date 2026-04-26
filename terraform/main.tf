terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.6"
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "sso_instance_arn" {
  type        = string
  description = "ARN de la instancia de IAM Identity Center"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "identity_store_id" {
  type        = string
  description = "ID del Identity Store (ej: d-1234567890)"
}
