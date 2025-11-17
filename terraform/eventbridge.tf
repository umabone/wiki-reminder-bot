resource "aws_iam_role" "scheduler-invoke-lambda" {
  name = "scheduler-invoke-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "scheduler.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "scheduler_invoke_lambda" {
  name = "scheduler-invoke-lambda-policy"
  role = aws_iam_role.scheduler_invoke.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = "lambda:InvokeFunction",
        Resource = aws_lambda_function.wiki_reminder_tf.arn
      }
    ]
  })
}

resource "aws_scheduler_schedule" "wiki_schedule" {
  name       = "wiki-reminder-schedule"
  group_name = "default"

  schedule_expression = "cron(0 21 * * ? *)"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.wiki_reminder_tf.arn
    role_arn = aws_iam_role.scheduler_invoke.arn
  }
}

