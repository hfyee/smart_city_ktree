provider "aws" {
  region = var.aws_region

  # No explicit `assume_role` block here on purpose: EDM_AWS_ROLE_01 has no
  # sts:AssumeRole permission on itself, so credentials that are ALREADY
  # that role (as in CI, see below) cannot assume it a second time.
  # Instead, whatever runs Terraform is expected to hand the AWS provider
  # credentials for EDM_AWS_ROLE_01 directly, via the normal AWS SDK
  # credential chain:
  #
  #  - GitLab CI: the pipeline exchanges its OIDC id_token for role
  #    credentials via AWS_ROLE_ARN + AWS_WEB_IDENTITY_TOKEN_FILE (see
  #    .gitlab-ci.yml) — the trust policy on EDM_AWS_ROLE_01 already allows
  #    AssumeRoleWithWebIdentity from this project's gitlab.com OIDC
  #    provider for the main/dev_hrj branches.
  #  - Local runs: configure an AWS CLI profile that assumes the role
  #    (role_arn + source_profile in ~/.aws/config, or `aws sso` +
  #    `aws configure set role_arn ...`), then `export AWS_PROFILE=...`.
  #    See README.md "Local credentials" for the exact profile snippet.

  # No provider-level default_tags: see locals.tf for why — it would cause
  # the AWS provider to try (and fail) to tag EBS volumes, which this role
  # has no ec2:CreateTags permission for. Tags are applied explicitly
  # per-resource instead, via local.common_tags.
}
