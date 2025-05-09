#!/bin/bash

#!/bin/bash

# This script is used to fetch the latest code from remote develop,
# then validate, build, and deploy the SAM project.
# It stops immediately if any command fails.

echo "Fetching latest changes from remote origin..."
git fetch origin && \
echo "Checking out local develop branch..." && \
git checkout develop && \
echo "Pulling latest changes from remote develop..." && \
git pull origin develop && \
echo "Git operations successful. Proceeding with SAM validation, build, and deployment." && \
sam validate --lint && \
echo "SAM template is valid" && \
sam build && \
echo "SAM project has been built locally" && \
sam deploy && \
echo "SAM project has been deployed to cloud" && \
echo "Trailing cloud watch.."
#sam logs --profile shinrai.devpost --cw-log-group /aws/lambda/jubilee-ekyc-backend-JubileeESBCallFn-XdPRK0bM4j2x --tail --filter "- platform - botocore"  | cut -d ' ' -f 3-
#sam logs --profile shinrai.devpost --cw-log-group /aws/lambda/jubilee-ekyc-backend-DocumentTextractFn-Xn49U6xdE1D7 --tail --filter "- platform - botocore"  | cut -d ' ' -f 3-
sam logs --profile shinrai.devpost --cw-log-group /aws/lambda/jubilee-ekyc-backend-UploadDocumentFn-lzEMRPRanrrO --tail --filter "- platform - botocore"  | cut -d ' ' -f 3-