# ---------------------------------------------------------------------------
# Lambda de revocación automática de HeimdALL
# Se invoca por EventBridge Scheduler cuando caduca un grant
# ---------------------------------------------------------------------------

# Empaqueta el handler como ZIP para subirlo a Lambda
data "archive_file" "revoke_lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../backend/app/revoke_handler.py"
  output_path = "${path.module}/revoke_handler.zip"
}

# Rol IAM para la Lambda de revocación
resource "aws_iam_role" "revoke_lambda_role" {
  name = "heimdall-revoke-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "revoke_lambda_policy" {
  name = "heimdall-revoke-policy"
  role = aws_iam_role.revoke_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sso-admin:DeleteAccountAssignment",
          "identitystore:GetUserId",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:UpdateItem",
          "dynamodb:PutItem",
        ]
        Resource = [
          "arn:aws:dynamodb:${var.aws_region}:*:table/heimdall-${var.environment}-grants",
          "arn:aws:dynamodb:${var.aws_region}:*:table/heimdall-${var.environment}-audit",
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Lambda de revocación
resource "aws_lambda_function" "revoke" {
  function_name    = "heimdall-revoke-${var.environment}"
  filename         = data.archive_file.revoke_lambda_zip.output_path
  source_code_hash = data.archive_file.revoke_lambda_zip.output_base64sha256
  handler          = "revoke_handler.lambda_handler"
  runtime          = "python3.12"
  role             = aws_iam_role.revoke_lambda_role.arn
  timeout          = 30

  environment {
    variables = {
      SSO_INSTANCE_ARN      = var.sso_instance_arn
      IDENTITY_STORE_ID     = var.identity_store_id
      DYNAMODB_TABLE_PREFIX = "heimdall"
    }
  }
}

# ---------------------------------------------------------------------------
# Rol IAM para EventBridge Scheduler
# Permite a EventBridge invocar la Lambda de revocación
# ---------------------------------------------------------------------------

resource "aws_iam_role" "scheduler_role" {
  name = "heimdall-scheduler-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_policy" {
  name = "heimdall-scheduler-invoke-policy"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = aws_lambda_function.revoke.arn
    }]
  })
}

# ---------------------------------------------------------------------------
# Outputs: ARNs necesarios para el backend (.env)
# ---------------------------------------------------------------------------

output "revoke_lambda_arn" {
  value       = aws_lambda_function.revoke.arn
  description = "ARN de la Lambda de revocación — añadir a REVOKE_LAMBDA_ARN en .env"
}

output "scheduler_role_arn" {
  value       = aws_iam_role.scheduler_role.arn
  description = "ARN del rol de EventBridge Scheduler — añadir a SCHEDULER_ROLE_ARN en .env"
}
