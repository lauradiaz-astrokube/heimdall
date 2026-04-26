# ---------------------------------------------------------------------------
# Tablas DynamoDB de HeimdALL
# Modo on-demand (PAY_PER_REQUEST) → sin coste si no se usa
# ---------------------------------------------------------------------------

locals {
  prefix = "heimdall-${var.environment}"
}

# Solicitudes de acceso
resource "aws_dynamodb_table" "access_requests" {
  name         = "${local.prefix}-requests"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  # GSI para consultar solicitudes por usuario
  attribute {
    name = "requestor_id"
    type = "S"
  }

  # GSI para consultar por estado (PENDING, APPROVED, REJECTED, EXPIRED)
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

# Grants activos (accesos concedidos y aún vigentes)
resource "aws_dynamodb_table" "active_grants" {
  name         = "${local.prefix}-grants"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  # TTL automático: DynamoDB elimina el item cuando expires_at llegue
  # (no revoca en Identity Center — eso lo hace EventBridge)
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = { Environment = var.environment }
}

# Log de auditoría (inmutable — no se borran items)
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
