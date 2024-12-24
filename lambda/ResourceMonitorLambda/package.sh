#!/bin/bash

# Default values for parameters
DEFAULT_LAMBDA_DIR="lambda"
DEFAULT_ZIP_FILE="lambda_package.zip"

# Accept parameters or use default values
LAMBDA_DIR="${1:-$DEFAULT_LAMBDA_DIR}"
ZIP_FILE="${2:-$DEFAULT_ZIP_FILE}"

# Remove existing zip file
if [ -f "$ZIP_FILE" ]; then
  rm "$ZIP_FILE"
fi

# Install dependencies into a temporary folder
TEMP_DIR="temp_build"
mkdir -p "$TEMP_DIR"
pip install -r "$LAMBDA_DIR/requirements.txt" -t "$TEMP_DIR" > /dev/null

# Copy the Lambda code into the temporary folder
cp "$LAMBDA_DIR/"*.py "$TEMP_DIR"

# Create the zip package
cd "$TEMP_DIR" || exit
zip -r "../$ZIP_FILE" . > /dev/null
cd - || exit

# Clean up
rm -rf "$TEMP_DIR"

echo "Lambda package created: $ZIP_FILE"
