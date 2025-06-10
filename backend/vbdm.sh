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

# Utility function to clear and trail logs for a specified log group
clear_and_trail_logs() {
  local log_group="$1"
  
  if [ -z "$log_group" ]; then
    echo "Error: Log group parameter is required"
    echo "Usage: clear_and_trail_logs <log-group-name>"
    return 1
  fi
  
  echo "Clearing logs for log group: $log_group"
  aws logs delete-log-stream --profile shinrai.devpost --log-group-name "$log_group" --log-stream-name $(aws logs describe-log-streams --profile shinrai.devpost --log-group-name "$log_group" --query 'logStreams[*].logStreamName' --output text) 2>/dev/null
  
  echo "Starting to trail logs for: $log_group"
  sam logs --profile shinrai.devpost --cw-log-group "$log_group" --tail --filter "- platform - botocore" | cut -d ' ' -f 3-
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
clear_and_trail_logs "/aws/lambda/jubilee-ekyc-backend-GovernmentVerificationFn-TCCetQ2FSY0n"