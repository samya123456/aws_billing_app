#!/bin/bash

# Variables

STACK_NAME="peng-176-resource-cost-monitor-stack"
ROLE_ARN="arn:aws:iam::905418490146:role/POC-Execution-Role-ML-DS"
SESSION_NAME="DeleteStackSession"

echo "Assuming role: $ROLE_ARN"

# Assume the role and capture temporary credentials
CREDS=$(aws sts assume-role --role-arn "$ROLE_ARN" --role-session-name "$SESSION_NAME" --query 'Credentials' --output json)


export AWS_ACCESS_KEY_ID=$(echo "$CREDS" | jq -r '.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo "$CREDS" | jq -r '.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo "$CREDS" | jq -r '.SessionToken')

echo "Starting Delete Stack"

aws cloudformation delete-stack --stack-name "$STACK_NAME"

aws sns delete-topic --topic-arn arn:aws:sns:us-east-1:905418490146:AWSCostLambdaSNSTopic
