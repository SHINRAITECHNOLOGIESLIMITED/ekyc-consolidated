#!/bin/bash

# This script is used to fetch the latest code from remote develop,
# then validate, build, and deploy the SAM project.
# It stops immediately if any command fails.

print_separator() {
  echo ""
  echo "--------------------------------------------------------"
  echo "TASK $1: $2"
  echo "--------------------------------------------------------"
}

print_separator 1 "Fetching latest changes from remote origin" && \
git fetch origin && \

print_separator 2 "Checking out local develop branch" && \
git checkout develop && \

print_separator 3 "Pulling latest changes from remote develop" && \
git pull origin develop && \

print_separator 4 "SAM validation with linting"
echo "Git operations successful. Proceeding with SAM validation, build, and deployment." && \
sam validate --lint && \
echo "SAM template is valid" && \

print_separator 5 "Building SAM project locally" && \
sam build && \
echo "SAM project has been built locally" && \

print_separator 6 "Deploying SAM project to cloud" && \
sam deploy && \
echo "SAM project has been deployed to cloud" && \

print_separator 7 "Trailing cloud watch logs" && \
echo "Trailing cloud watch.." && \
#sam logs --profile shinrai.devpost --cw-log-group /aws/lambda/jubilee-ekyc-backend-JubileeESBCallFn-XdPRK0bM4j2x --tail --filter "- platform - botocore"  | cut -d ' ' -f 3-
#sam logs --profile shinrai.devpost --cw-log-group /aws/lambda/jubilee-ekyc-backend-DocumentTextractFn-Xn49U6xdE1D7 --tail --filter "- platform - botocore"  | cut -d ' ' -f 3-
sam logs --profile shinrai.devpost --cw-log-group /aws/lambda/jubilee-ekyc-backend-UploadDocumentFn-lzEMRPRanrrO --tail --filter "- platform - botocore"  | cut -d ' ' -f 3-