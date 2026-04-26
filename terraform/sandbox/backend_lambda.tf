# ---------------------------------------------------------------------------
# Backend Lambda de HeimdALL (FastAPI via Mangum)
# Expuesto con Lambda Function URL — sin coste adicional vs API Gateway
# ---------------------------------------------------------------------------

resource "aws_iam_role" "backend_lambda_role" {
  name = "heimdall-backend-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "backend_lambda_policy" {
  name = "heimdall-backend-lambda-policy"
  role = aws_iam_role.backend_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem",
          "dynamodb:Query", "dynamodb:Scan",
        ]
        Resource = [
          "arn:aws:dynamodb:${var.aws_region}:*:table/heimdall-${var.environment}-*",
          "arn:aws:dynamodb:${var.aws_region}:*:table/heimdall-${var.environment}-*/index/*",
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["scheduler:CreateSchedule", "scheduler:DeleteSchedule"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = "sts:AssumeRole"
        Resource = "arn:aws:iam::${var.main_account_id}:role/heimdall-identity-center-role"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_lambda_function" "backend" {
  function_name    = "heimdall-backend-${var.environment}"
  filename         = "${path.module}/backend_lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/backend_lambda.zip")
  handler          = "app.main.lambda_handler"
  runtime          = "python3.12"
  role             = aws_iam_role.backend_lambda_role.arn
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      ENTRA_TENANT_ID          = var.entra_tenant_id
      OIDC_CLIENT_ID           = var.oidc_client_id
      SSO_INSTANCE_ARN         = var.sso_instance_arn
      IDENTITY_STORE_ID        = var.identity_store_id
      IDENTITY_CENTER_ROLE_ARN = "arn:aws:iam::${var.main_account_id}:role/heimdall-identity-center-role"
      DYNAMODB_TABLE_PREFIX    = "heimdall"
      REVOKE_LAMBDA_ARN        = aws_lambda_function.revoke.arn
      SCHEDULER_ROLE_ARN       = aws_iam_role.scheduler_role.arn
      CORS_ORIGINS             = "[\"https://lauradiaz-astrokube.github.io\"]"
    }
  }
}

# Function URL — HTTPS gratuito sin API Gateway
resource "aws_lambda_function_url" "backend" {
  function_name      = aws_lambda_function.backend.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = true
    allow_origins     = ["https://lauradiaz-astrokube.github.io"]
    allow_methods     = ["*"]
    allow_headers     = ["Content-Type", "Authorization"]
    max_age           = 86400
  }
}

output "backend_function_url" {
  value       = aws_lambda_function_url.backend.function_url
  description = "URL del backend — añadir como VITE_API_URL en GitHub Variables"
}
