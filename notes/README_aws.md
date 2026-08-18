# 0. Verify your profile exists before you start
aws configure list-profiles

## If profile isn't in that list, create it
aws configure --profile EDM_IAM_03
## else if you already ran aws configure before
export AWS_PROFILE=EDM_IAM_03 
export AWS_PROFILE=EDM_AWS_ROLE_01
aws configure # just to confirm

Assume your assigned role by adding a new profile in ~/.aws/config

# 1. Confirm your identity and your subnet
aws sts get-caller-identity --profile EDM_IAM_03
aws ec2 describe-subnets --subnet-ids subnet-0853cb9556de61de5 --profile EDM_AWS_ROLE_01
## Note AvailableIpAddressCount — should be 11 on a fresh /28

# 2. Create your own security group for VPC
aws ec2 describe-security-groups --profile EDM_IAM_03
(Result: "not authorized to perform this operation.")

## Get <YOUR_VPC_CIDR> via
aws ec2 describe-vpcs --vpc-ids vpc-07d617bf1d097edcd --query 'Vpcs[0].CidrBlock' --output text --profile EDM_AWS_ROLE_01

(Result: 10.42.0.0/16)

## Check route table associated with your subnet
aws ec2 describe-instances \
    --instance-ids i-01c4b47711b9b37f2 \
    --query "Reservations[0].Instances[0].[VpcId,SubnetId,PrivateIpAddress,PublicIpAddress]" \
    --output table \
    --profile EDM_AWS_ROLE_01

aws ec2 describe-route-tables \
    --filters Name=association.subnet-id,Values=subnet-0853cb9556de61de5 \
    --query "RouteTables[0].RouteTableId" \
    --output text \
    --profile EDM_AWS_ROLE_01

(result: rtb-0da87746519316583)

aws ec2 describe-route-tables \
    --route-table-ids rtb-0da87746519316583 \
    --query "RouteTables[0].Routes[*].[DestinationCidrBlock,GatewayId,NatGatewayId,State]" \
    --output table
    --profile EDM_AWS_ROLE_01

(Results: not authorized to perform: ec2:DescribeRouteTables)

## Get the security group attached to your instance
aws ec2 describe-instances \
    --instance-ids i-01c4b47711b9b37f2 \
    --query "Reservations[0].Instances[0].SecurityGroups[*].[GroupId,GroupName]" \
    --output table \
    --profile EDM_AWS_ROLE_01

## Inspect the security group
aws ec2 describe-security-groups \
    --group-ids sg-0a3d787e2e1df274c  \
    --query "SecurityGroups[0].IpPermissions" \
    --output json \
    --profile EDM_AWS_ROLE_01

## Add an SSH inbound rule allowing only your machine
curl https://checkip.amazonaws.com

aws ec2 authorize-security-group-ingress \
    --group-id sg-0a3d787e2e1df274c \
    --protocol tcp \
    --port 22 \
    --cidr 119.234.59.9/32 \
    --profile EDM_AWS_ROLE_01

## /32 means only that one public IP address
## verify:
nc -vz ec2-13-212-197-148.ap-southeast-1.compute.amazonaws.com 22

## Create your own key pair
aws ec2 create-key-pair \
  --key-name "edm_iam_03" \
  --tag-specifications "ResourceType=key-pair,Tags=[{Key=GroupTag,Value=01}]" \
  --query 'KeyMaterial' --output text \
  --profile EDM_AWS_ROLE_01 > edm_iam_03.pem

chmod 400 edm_iam_03.pem

(Result: this pem didn't work; key pair was created at the point of EC2 creation by Mr Heng.)

## Check which key pair was used
aws ec2 describe-instances \
    --instance-ids i-01c4b47711b9b37f2 \
    --query "Reservations[0].Instances[0].KeyName" \
    --output text \
    --profile EDM_AWS_ROLE_01

(Result: edm-group01-key)

# 3. Find a launchable AMI
aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=al2023-ami-*-x86_64" "Name=state,Values=available" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text \
  --profile EDM_AWS_ROLE_01

(Return result: ami-0bda501dba2e3a0ba)

aws ec2 describe-images \
  --region ap-southeast-1 \
  --image-ids ami-0bda501dba2e3a0ba \
  --query 'Images[0].[Name,Description,PlatformDetails]' \
  --output table \
	--profile EDM_AWS_ROLE_01

# 4. Launch an instance into your subnet
aws ec2 run-instances \
  --image-id ami-0bda501dba2e3a0ba \
  --instance-type t3.micro \
  --subnet-id subnet-0853cb9556de61de5 \
  --security-group-ids sg-061684f43fd4920cb \
  --key-name "edm_iam_03-project" \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=GroupTag,Value=01}]' \
  --associate-public-ip-address \
  --profile EDM_AWS_ROLE_01

(Result: created "InstanceId": "i-010241bcdc5a34057")

# 5. Inspect the instance
aws ec2 describe-instances \
  --instance-ids i-01f9c9d74e3732bbe \
  --query 'Reservations[0].Instances[0].{State:State.Name,Type:InstanceType,Subnet:SubnetId,Private:PrivateIpAddress}' \
  --profile EDM_AWS_ROLE_01

## To list the EC2 instances in your profile
aws ec2 describe-instances --profile EDM_AWS_ROLE_01 | grep InstanceId

## Also display their status and public IP address
aws ec2 describe-instances --region ap-southeast-1 \
    --query "Reservations[*].Instances[*].{ID:InstanceId,Status:State.Name,PublicIP:PublicIpAddress}" \
    --output table \
    --profile EDM_AWS_ROLE_01

# 6. Stop / start the instance
aws ec2 stop-instances --instance-ids i-01f9c9d74e3732bbe --profile EDM_AWS_ROLE_01
aws ec2 start-instances --instance-ids i-01f9c9d74e3732bbe --profile EDM_AWS_ROLE_01

# 7. Terminate the instance
# No need to stop instance before terminating it. AWS automatically handles the shutdown process for you. 
aws ec2 terminate-instances --instance-ids i-01f9c9d74e3732bbe --profile EDM_AWS_ROLE_01

# ssh to EC2 instance
## Find your internet gateway
aws ec2 describe-internet-gateways \
    --filters Name=attachment.vpc-id,Values=vpc-07d617bf1d097edcd \
    --query "InternetGateways[0].InternetGatewayId" \
    --output text

## big EC2 instance for pipeline
ssh -i ./edm-group01-key.pem ec2-user@13.212.197.148
