locals {
  # Applied explicitly per-resource instead of via provider-level
  # `default_tags` (see provider.tf for why): default_tags cause the AWS
  # provider to also issue a follow-up ec2:CreateTags call on any EBS
  # volumes created via root_block_device/ebs_block_device, and
  # EDM_AWS_ROLE_01 has no ec2:CreateTags grant on volume/* — only on
  # instance/security-group/key-pair. Leaving root_block_device/
  # ebs_block_device `tags` unset (see ec2.tf) means no tags get computed
  # for the volumes, so the provider skips that call entirely.
  common_tags = {
    ProjectTag  = "EDM"
    GroupTag    = var.group_tag
    SemesterTag = "AY26_S1"
    ManagedBy   = "terraform"
  }
}
