export AWS_PROFILE=EDM_AWS_ROLE_01

terraform init
terraform validate
terraform fmt         # will modify files to fix linting style
terraform fmt -check  # check only
terraform plan -out=smart_city_ktree.plan
terraform show "smart_city_ktree.plan"
terraform apply "smart_city_ktree.plan"

# Verify
terraform state list

terraform output -raw private_key > edm-group01-key.pem
chmod 400 edm-group01-key.pem
