#!/bin/bash

DEFAULT_LAMBDA_DIR="lambda/resource_cost_monitoring_lambda_deploy"
DEFAULT_ZIP_FILE="lambda_package.zip"
S3BucketName="peng-176-cost-calculator-python-bucket"
S3BucketDeployRegion="us-east-1" ##change region based on working aws region

# Accept parameters or use default values
LAMBDA_DIR="${1:-$DEFAULT_LAMBDA_DIR}"
ZIP_FILE="${2:-$DEFAULT_ZIP_FILE}"

# Remove existing zip file
if [ -f "$ZIP_FILE" ]; then
  rm "$ZIP_FILE"
  echo "removing zip file"
fi

# Install dependencies into a temporary folder
TEMP_DIR="temp_build"
mkdir -p "$TEMP_DIR"
pip3 install -r "$LAMBDA_DIR/requirements.txt" -t "$TEMP_DIR" > /dev/null

# Copy the Lambda code into the temporary folder
cp "$LAMBDA_DIR/"* "$TEMP_DIR"

# Create the zip package
cd "$TEMP_DIR" || exit
zip -r "../$ZIP_FILE" . > /dev/null
cd - || exit

if aws s3 ls $S3BucketName 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Creating S3 bucket."
    aws s3api create-bucket --bucket $S3BucketName --region ${S3BucketDeployRegion}
    else
    echo "Bucket already exists..."
fi

# enabling S3 bucket versioning

# echo "Enable versioning for Deployment bucket"
# aws s3api put-bucket-versioning --bucket $S3BucketName --versioning-configuration Status=Enabled
aws s3 cp ${ZIP_FILE} s3://${S3BucketName}/

rm -rf "$TEMP_DIR"

echo "Lambda package created: $ZIP_FILE"
