resource "aws_security_group" "edm01" {
  name        = "edm-group01-sg"
  description = "SSH + inter-instance DB access for EDM group 01"
  vpc_id      = var.vpc_id

  # Created inside the lab VPC with GroupTag=01 to satisfy
  # CreateSecurityGroupInLabVpc / CreateOwnSecurityGroup conditions.

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_allowed_cidrs
  }

  # DB ports reachable only from other instances in this same SG
  # (i.e. the 3 worker EC2s talking to the DB host) — not exposed publicly.
  ingress {
    description = "MongoDB (intra-group only)"
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description = "Neo4j HTTP + Bolt (intra-group only)"
    from_port   = 7474
    to_port     = 7474
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description = "Neo4j Bolt (intra-group only)"
    from_port   = 7687
    to_port     = 7687
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description = "ChromaDB (intra-group only)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    self        = true
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Deliberately just local.common_tags, no extra Name tag: this SG was
  # already created (under an earlier provider default_tags setup) with
  # exactly this tag set. Adding any new tag key here makes the AWS
  # provider issue a partial CreateTags update containing only the new
  # key(s) — which excludes GroupTag from that specific API call and fails
  # the role's aws:RequestTag/GroupTag=01 condition (it's evaluated per
  # call, not against the resource's full tag set). Keeping tags identical
  # to what's already on the resource means no update call happens at all.
  tags = local.common_tags

  lifecycle {
    create_before_destroy = true
  }
}
