# 0. Verify your profile exists before you start
aws configure list-profiles

## If profile isn't in that list, create it
aws configure --profile EDM_IAM_03
## else if you already ran aws configure before
export AWS_PROFILE=EDM_IAM_03 
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

SG_ID=$(aws ec2 create-security-group \
  --group-name "learner-09-cli-practical" \
  --description "Learner 09 CLI practical" \
  --vpc-id vpc-0ba28a3f8ae00b516 \
  --tag-specifications "ResourceType=security-group,Tags=[{Key=LearnerId,Value=09}]" \
  --query 'GroupId' --output text \
  --profile learner-09)
  
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --ip-permissions 'IpProtocol=icmp,FromPort=-1,ToPort=-1,IpRanges=[{CidrIp=10.42.0.0/16,Description="ICMP from within lab VPC"}]' \
  --profile learner-09

## route table associated with your subnet
rtb-07f1ebb6afbb0661c

## Create your own key pair
aws ec2 create-key-pair \
  --key-name "edm_iam_03-project" \
  --tag-specifications "ResourceType=key-pair,Tags=[{Key=GroupTag,Value=01}]" \
  --query 'KeyMaterial' --output text \
  --profile EDM_AWS_ROLE_01 > edm_iam_03-project.pem

chmod 400 edm_iam_03-project.pem

# 3. Find a launchable AMI
aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=al2023-ami-*-x86_64" "Name=state,Values=available" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text \
  --profile EDM_AWS_ROLE_01

(Return result: ami-0bda501dba2e3a0ba)

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
  --profile learner-09

## To list the EC2 instances in your profile
aws ec2 describe-instances --profile EDM_AWS_ROLE_01 | grep InstanceId

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

ssh -i edm_iam_03-project.pem ec2-user@13.250.126.59
ssh -i edm_iam_03-project.pem ubuntu@13.250.126.59
