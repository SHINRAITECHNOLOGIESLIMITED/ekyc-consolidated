#!/bin/bash

# This script is used to validate, then build, then deploy then monitor the SAM project.It stops when one process fails
sam validate --lint && \
sam build --beta-features && \
sam deploy && \
# sam logs --profile shinrai.devpost --cw-log-group /aws/lambda/jubilee-ekyc-backend-KRAValidateIDNumberFn-yR4TPJIncFTc --tail --filter "- platform - botocore"  | cut -d ' ' -f 3-
sam logs --profile shinrai.devpost --cw-log-group /aws/lambda/jubilee-ekyc-backend-IPRSSearchFn-aO44sw1R7hkH --tail --filter "- platform - botocore"  | cut -d ' ' -f 3-