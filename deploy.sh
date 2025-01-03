#!/bin/bash

# Variables
LAMBDA_ROOT_DIR="./lambda/resource_cost_monitoring"
STACK_NAME="ResourceCostMonitor"
TEMPLATE_FILE="template.yaml"
PARAM_FILE="parameters.json"
PACKAGE_SCRIPT="$LAMBDA_ROOT_DIR/package.sh"
ZIP_FILE="$LAMBDA_ROOT_DIR/lambda_package.zip"

# Step 1: Run the packaging script
if [ -f "$PACKAGE_SCRIPT" ]; then
  echo "Running packaging script..."
  chmod +x "$PACKAGE_SCRIPT"
  ./"$PACKAGE_SCRIPT" "$LAMBDA_ROOT_DIR" "$ZIP_FILE"
  if [ $? -ne 0 ]; then
    echo "Error: Packaging script failed."
    exit 1
  fi
else
  echo "Error: Packaging script ($PACKAGE_SCRIPT) not found."
  exit 1
fi

if [ ! -f "$ZIP_FILE" ]; then
  echo "Error: Lambda package ($ZIP_FILE) not found."
  exit 1
fi

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
