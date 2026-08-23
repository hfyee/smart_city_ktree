# Copy to terraform.tfvars and fill in — terraform.tfvars is gitignored.

ssh_allowed_cidrs = [
  "119.234.59.9/32", # e.g. a team member's home/office IP
  # "10.42.0.0/16",  # or the campus VPN / internal CIDR, once confirmed
]

# Leave as default (true) once the Internet Gateway has been attached to
# vpc-07d617bf1d097edcd; set to false if you want private-IP-only instances.
# assign_public_ip = true
