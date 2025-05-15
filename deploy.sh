#!/bin/bash

# Variables
LAMBDA_ROOT_DIR="./lambda/resource_cost_monitoring_lambda_deploy"
STACK_NAME="peng-176-resource-cost-monitor-stack"
TEMPLATE_FILE="./iac/template.yaml"
PARAM_FILE="./iac/values/parameters.json"
PACKAGE_SCRIPT="$LAMBDA_ROOT_DIR/package.sh"
ZIP_FILE="$LAMBDA_ROOT_DIR/lambda_package_123.zip"

# Step 1: Run the packaging script
if [ -f "$PACKAGE_SCRIPT" ]; then
  echo "Running packaging script..."
  chmod +x "$PACKAGE_SCRIPT"
  ./"$PACKAGE_SCRIPT" $LAMBDA_ROOT_DIR $ZIP_FILE
  if [ $? -ne 0 ]; then
    echo "Error: Packaging script failed."
    exit 1
  fi
else
  echo "Error: Packaging script ($PACKAGE_SCRIPT) not found."
  exit 1
fi

S3BucketName="peng-176-cost-monitoring-lambda-source-bucket"
S3BucketDeployRegion="us-east-1"
LambdaSourceFile="./lambda/lambda_source_file/config.yaml"

if aws s3 ls $S3BucketName 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating S3 bucket."
    aws s3api create-bucket --bucket $S3BucketName --region ${S3BucketDeployRegion}
    else
    echo "Bucket already exists..."
fi

echo "Copying Lambda source file into S3 bucket"

aws s3 cp ${LambdaSourceFile} s3://${S3BucketName}/version-1/


ROLE_ARN="arn:aws:iam::905418490146:role/POC-Execution-Role-ML-DS"
SESSION_NAME="DeploySessionWithAssumeRole"

echo "Assuming role: $ROLE_ARN"

# Assume the role and capture temporary credentials
CREDS=$(aws sts assume-role --role-arn "$ROLE_ARN" --role-session-name "$SESSION_NAME" --query 'Credentials' --output json)


export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | jq -r '.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | jq -r '.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo "$CREDS" | jq -r '.SessionToken')

echo "Starting deployment"

if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME" > /dev/null 2>&1; then
  echo "Stack does not exist. Creating stack..."
  aws cloudformation create-stack --stack-name "$STACK_NAME" --template-body file://"$TEMPLATE_FILE" --parameters file://"$PARAM_FILE" --capabilities CAPABILITY_NAMED_IAM
  aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME"
  echo "Stack created successfully."
else
  echo "Stack exists. Updating stack..."
  aws cloudformation update-stack --stack-name "$STACK_NAME" --template-body file://"$TEMPLATE_FILE" --parameters file://"$PARAM_FILE" --capabilities CAPABILITY_NAMED_IAM
  aws cloudformation wait stack-update-complete --stack-name "$STACK_NAME"
  echo "Stack updated successfully."
fi


