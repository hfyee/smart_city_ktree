variable "aws_region" {
  description = "AWS region. Fixed to the lab region — the role has no permissions elsewhere."
  type        = string
  default     = "ap-southeast-1"
}

variable "assume_role_arn" {
  description = "IAM role Terraform runs as. Owned/created by a separate Terraform project — this project only consumes it. Not referenced in an `assume_role` provider block (see provider.tf); documented here for reference and for local AWS CLI profile setup (README.md)."
  type        = string
  default     = "arn:aws:iam::200810865757:role/lab-groups/EDM_AWS_ROLE_01"
}

variable "group_tag" {
  description = "Value for GroupTag. Every EC2/SG/key-pair action the role can take is gated on aws:RequestTag/GroupTag or aws:ResourceTag/GroupTag == this value, so it must stay \"01\"."
  type        = string
  default     = "01"
}

variable "vpc_id" {
  description = "Existing lab VPC. The role can only CreateSecurityGroup inside this VPC."
  type        = string
  default     = "vpc-07d617bf1d097edcd"
}

variable "subnet_id" {
  description = "Existing lab subnet. The role's RunInstances permission is scoped to this single subnet only — it cannot launch elsewhere."
  type        = string
  default     = "subnet-0853cb9556de61de5"
}

variable "assign_public_ip" {
  description = "Whether instances get a public IP at launch. Requires the Internet Gateway that is being added to the VPC separately (out of scope of this project) plus the subnet's own auto-assign-public-IP setting or an explicit override here."
  type        = bool
  default     = true
}

variable "ssh_allowed_cidrs" {
  description = "CIDR blocks allowed to SSH (port 22) into the instances. Restrict this to the team's actual source IPs / VPN range before applying — do not leave it open to 0.0.0.0/0."
  type        = list(string)

  validation {
    condition     = length(var.ssh_allowed_cidrs) > 0
    error_message = "Set ssh_allowed_cidrs in terraform.tfvars to your team's actual source IP(s)/VPN CIDR before applying — it must not be left empty or 0.0.0.0/0."
  }
}

variable "db_host_instance_type" {
  description = "Instance type for the single EC2 hosting chromadb, mongodb and neo4j. t3.xlarge = 4 vCPU / 16GiB RAM."
  type        = string
  default     = "t3.xlarge"
}

variable "db_host_volume_size_gb" {
  description = "Size (GB) of the dedicated data volume on the DB host, mounted at /data for all three databases' persistent storage."
  type        = number
  default     = 100
}

variable "worker_instance_type" {
  description = "Instance type for the 3 general-purpose small EC2s."
  type        = string
  default     = "t3.small"
}

variable "worker_count" {
  description = "Number of small worker EC2 instances."
  type        = number
  default     = 3
}

variable "auto_shutdown_hour_utc" {
  description = "Hour (0-23, in the instance's local/UTC time per AMI default) at which the daily auto-shutdown cron fires. Amazon Linux defaults to UTC."
  type        = number
  default     = 1
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size (GB) for every instance. Must be >= the current Amazon Linux 2023 AMI's root snapshot size (30GB at last check) or RunInstances fails with InvalidBlockDeviceMapping — bump this if a newer AMI raises that floor further."
  type        = number
  default     = 30
}
