terraform {
  # >= 1.10 required for the S3 backend's native `use_lockfile` locking
  # (backend.tf) — this role has no DynamoDB permissions for the older
  # lock-table approach.
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
