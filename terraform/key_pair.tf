# EDM_AWS_ROLE_01 has ec2:CreateKeyPair (tagged GroupTag=01) but no IAM
# permissions, so SSM Session Manager isn't an option — SSH key pair is the
# access mechanism for every team member's IAM user assuming this role.

resource "tls_private_key" "edm01" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "edm01" {
  key_name   = "edm-group01-key"
  public_key = tls_private_key.edm01.public_key_openssh
  tags       = local.common_tags
}

# The private key is never written to disk by Terraform (avoids it ever
# landing in the repo). Retrieve it explicitly after apply:
#   terraform output -raw private_key > edm-group01-key.pem
#   chmod 400 edm-group01-key.pem       # macOS/Linux
output "private_key" {
  value     = tls_private_key.edm01.private_key_pem
  sensitive = true
}
