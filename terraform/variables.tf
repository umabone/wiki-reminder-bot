variable "WEBHOOK_URL" {
  description = "Discord webhook URL supplied through TF_VAR_WEBHOOK_URL."
  type        = string
  sensitive   = true

  validation {
    condition     = length(trimspace(var.WEBHOOK_URL)) > 0
    error_message = "WEBHOOK_URL must be set to a non-empty value."
  }
}
