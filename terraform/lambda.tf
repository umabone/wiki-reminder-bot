resource "aws_iam_role" "lambda-basic-exec" {
  name = "lambda-basic-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda-basic-exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "wiki_reminder_tf" {
  function_name = "wiki-reminder-tf"
  handler       = "send_discord_notification.lambda_handler"
  runtime       = "python3.12"

  filename         = "${path.module}/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda.zip")

  role = aws_iam_role.lambda-basic-exec.arn

  timeout = 20

  environment {
    variables = {
      WEBHOOK_URL = var.WEBHOOK_URL
    }
  }
}
