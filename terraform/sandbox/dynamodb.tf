# ---------------------------------------------------------------------------
# Tablas DynamoDB de HeimdALL — cuenta sandbox
# ---------------------------------------------------------------------------

locals {
  prefix = "heimdall-${var.environment}"
}

resource "aws_dynamodb_table" "access_requests" {
  name         = "${local.prefix}-requests"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "requestor_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name            = "by-requestor"
    hash_key        = "requestor_id"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "by-status"
    hash_key        = "status"
    projection_type = "ALL"
  }

  tags = { Environment = var.environment }
}

resource "aws_dynamodb_table" "active_grants" {
  name         = "${local.prefix}-grants"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = { Environment = var.environment }
}

resource "aws_dynamodb_table" "audit_log" {
  name         = "${local.prefix}-audit"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  range_key    = "timestamp"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = { Environment = var.environment }
}
