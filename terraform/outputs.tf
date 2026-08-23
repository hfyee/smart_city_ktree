output "db_host_public_ip" {
  description = "Public IP of the DB host (chromadb, mongodb, neo4j). Null until the Internet Gateway is attached to the VPC."
  value       = aws_instance.db_host.public_ip
}

output "db_host_private_ip" {
  value = aws_instance.db_host.private_ip
}

output "worker_public_ips" {
  value = aws_instance.worker[*].public_ip
}

output "worker_private_ips" {
  value = aws_instance.worker[*].private_ip
}

output "neo4j_password" {
  value     = random_password.neo4j.result
  sensitive = true
}

output "ssh_key_name" {
  value = aws_key_pair.edm01.key_name
}
