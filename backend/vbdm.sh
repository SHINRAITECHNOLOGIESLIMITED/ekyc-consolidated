#!/bin/bash

# This script is used to validate, then build, then deploy then monitor the SAM project.It stops when one process fails
sam validate --lint && \
sam build && \
sam deploy && \
#sam logs --profile shinrai.devpost --cw-log-group /aws/lambda/jubilee-ekyc-backend-JubileeESBCallFn-XdPRK0bM4j2x --tail --filter "- platform - botocore"  | cut -d ' ' -f 3-
#sam logs --profile shinrai.devpost --cw-log-group /aws/lambda/jubilee-ekyc-backend-DocumentTextractFn-Xn49U6xdE1D7 --tail --filter "- platform - botocore"  | cut -d ' ' -f 3-
sam logs --profile shinrai.devpost --cw-log-group /aws/lambda/jubilee-ekyc-backend-UploadDocumentFn-lzEMRPRanrrO --tail --filter "- platform - botocore"  | cut -d ' ' -f 3-