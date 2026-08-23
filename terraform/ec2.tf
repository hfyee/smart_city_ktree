data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "random_password" "neo4j" {
  length  = 20
  special = false
}

# ---------------------------------------------------------------------------
# DB host: 1 EC2 running chromadb, mongodb and neo4j as Docker containers,
# each with its own persistent storage on a dedicated data volume.
# ---------------------------------------------------------------------------
resource "aws_instance" "db_host" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.db_host_instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.edm01.id]
  key_name                    = aws_key_pair.edm01.key_name
  associate_public_ip_address = var.assign_public_ip

  root_block_device {
    volume_size = var.root_volume_size_gb
    volume_type = "gp3"
  }

  # Attached as /dev/xvdb and formatted/mounted at /data by db_host_setup.sh
  ebs_block_device {
    device_name = "/dev/xvdb"
    volume_size = var.db_host_volume_size_gb
    volume_type = "gp3"
  }

  user_data = <<-EOT
    #!/bin/bash
    ${templatefile("${path.module}/scripts/auto_shutdown.tpl.sh", { shutdown_hour = var.auto_shutdown_hour_utc })}
    ${templatefile("${path.module}/scripts/db_host_setup.tpl.sh", { neo4j_password = random_password.neo4j.result })}
  EOT

  # Deliberately no `tags` on root_block_device/ebs_block_device above —
  # see locals.tf. Instance-level tags below are fine: EDM_AWS_ROLE_01 does
  # have ec2:CreateTags on instance/* (tagged GroupTag=01).
  tags = merge(local.common_tags, {
    Name = "edm-group01-db-host"
    Role = "chromadb-mongodb-neo4j"
  })
}

# ---------------------------------------------------------------------------
# 3 general-purpose small worker EC2 instances.
# ---------------------------------------------------------------------------
resource "aws_instance" "worker" {
  count = var.worker_count

  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.worker_instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [aws_security_group.edm01.id]
  key_name                    = aws_key_pair.edm01.key_name
  associate_public_ip_address = var.assign_public_ip

  root_block_device {
    volume_size = var.root_volume_size_gb
    volume_type = "gp3"
  }

  user_data = <<-EOT
    #!/bin/bash
    ${templatefile("${path.module}/scripts/auto_shutdown.tpl.sh", { shutdown_hour = var.auto_shutdown_hour_utc })}
  EOT

  # Deliberately no `tags` on root_block_device above — see locals.tf.
  tags = merge(local.common_tags, {
    Name = "edm-group01-worker-${count.index + 1}"
    Role = "general-purpose"
  })
}
