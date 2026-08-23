# Remote state is required because Terraform runs inside stateless GitLab CI
# job containers — a local backend would lose state between the plan and
# apply jobs (and between pipelines).
#
# Bucket is intentionally NOT hardcoded here: it comes from the existing
# CI/CD variable TF_STATE_BUCKET (currently "edm-s3-01-200810865757" — the
# one bucket EDM_AWS_ROLE_01 actually has S3 access to) via
# `-backend-config` at init time (see .gitlab-ci.yml / README.md "Running
# locally"). Everything else is fixed.
#
# use_lockfile uses S3's own conditional-write locking (Terraform >= 1.10),
# avoiding the need for a DynamoDB lock table.
terraform {
  backend "s3" {
    key          = "terraform/edm-group01-ec2.tfstate"
    region       = "ap-southeast-1"
    use_lockfile = true
  }
}
