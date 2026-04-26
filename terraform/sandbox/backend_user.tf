# ---------------------------------------------------------------------------
# IAM user para el backend en local (desarrollo)
# En producción se sustituiría por el execution role de Lambda/ECS
# ---------------------------------------------------------------------------

resource "aws_iam_user" "heimdall_backend" {
  name = "heimdall-backend"
  tags = { Environment = var.environment }
}

resource "aws_iam_access_key" "heimdall_backend" {
  user = aws_iam_user.heimdall_backend.name
}

resource "aws_iam_user_policy" "heimdall_backend_policy" {
  name = "heimdall-backend-policy"
  user = aws_iam_user.heimdall_backend.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # DynamoDB en sandbox
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan",
        ]
        Resource = [
          "arn:aws:dynamodb:${var.aws_region}:*:table/heimdall-${var.environment}-*",
          "arn:aws:dynamodb:${var.aws_region}:*:table/heimdall-${var.environment}-*/index/*",
        ]
      },
      {
        # EventBridge Scheduler en sandbox
        Effect   = "Allow"
        Action   = ["scheduler:CreateSchedule", "scheduler:DeleteSchedule"]
        Resource = "*"
      },
      {
        # Asumir el role de Identity Center en la cuenta main
        Effect   = "Allow"
        Action   = "sts:AssumeRole"
        Resource = "arn:aws:iam::${var.main_account_id}:role/heimdall-identity-center-role"
      }
    ]
  })
}

output "backend_access_key_id" {
  value       = aws_iam_access_key.heimdall_backend.id
  description = "AWS_ACCESS_KEY_ID para el .env del backend"
}

output "backend_secret_access_key" {
  value       = aws_iam_access_key.heimdall_backend.secret
  sensitive   = true
  description = "AWS_SECRET_ACCESS_KEY para el .env del backend — terraform output -raw backend_secret_access_key"
}
