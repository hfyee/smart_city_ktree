# Check if an Amazon S3 bucket exists
## 'head-bucket' targets a specific bucket to check its existence and permissions, 
## while 'list-buckets' returns a comprehensive list of all S3 buckets owned by your AWS account.
aws s3api head-bucket --bucket edm-s3-01-200810865757 --profile EDM_AWS_ROLE_01
# aws s3api list-buckets --profile EDM_AWS_ROLE_01

## List the files in S3 bucket
## only evaluates actual files; does not show folder names
aws s3 ls s3://edm-s3-01-200810865757 --profile EDM_AWS_ROLE_01
aws s3 ls s3://edm-s3-01-200810865757/raw_data --recursive --profile EDM_AWS_ROLE_01

# Get overview of existing S3 bucket settings

## View the IAM access policy attached to the bucket
aws s3api get-bucket-policy --bucket edm-s3-01-200810865757 --profile EDM_AWS_ROLE_01

## Check if public access to the bucket is blocked
aws s3api get-public-access-block --bucket edm-iam-09-s3-09-200810865757

## Show default server-side encryption configurations
aws s3api get-bucket-encryption --bucket edm-s3-01-200810865757

## Check bucket ownership and ACL permissions
aws s3api get-bucket-acl --bucket edm-s3-01-200810865757 --profile EDM_AWS_ROLE_01

## View configuration if the bucket hosts a static website
aws s3api get-bucket-website --bucket edm-iam-09-s3-09-200810865757

## See what triggers AWS Lambda, SQS, or SNS events
aws s3api get-bucket-notification-configuration --bucket edm-s3-01-200810865757

## View all configurations at once
BUCKET="edm-s3-01-200810865757"; for cmd in location versioning encryption public-access-block acl policy lifecycle-configuration website notification-configuration cors; do echo "=== Bucket $cmd ==="; aws s3api get-bucket-$cmd --bucket $BUCKET 2>&1; done

BUCKET="edm-s3-01-200810865757"; for cmd in encryption public-access-block acl policy website; do echo "=== Bucket $cmd ==="; aws s3api get-bucket-$cmd --bucket $BUCKET > s3_settings.log 2>&1; done

# Upload files to S3 bucket
aws s3 cp my_local_file.txt s3://edm-s3-01-200810865757/
aws s3 cp my_local_file.txt s3://edm-s3-01-200810865757/renamed_file.txt
## Upload folder or multiple files 
aws s3 cp raw_data s3://edm-s3-01-200810865757/raw_data --recursive --profile EDM_AWS_ROLE_01
## Uploads only new or modified files (sync folder changes)
aws s3 sync /path/to/local/folder s3://edm-s3-01-200810865757/
# Rename folder in S3 bucket
aws s3 mv s3://edm-s3-01-200810865757/data/ s3://edm-s3-01-200810865757/raw_data/ --recursive --profile EDM_AWS_ROLE_01
# Delete file from S3 bucket
aws s3 rm s3://edm-s3-01-200810865757/smart_city_dataset_weather_data.json  --
profile EDM_AWS_ROLE_01
