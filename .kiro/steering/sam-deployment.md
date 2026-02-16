---
inclusion: fileMatch
fileMatchPattern: "**/template.yaml,**/samconfig.toml"
---

# SAM Deployment Guide

This steering file is automatically included when working with SAM template files.

## SAM Template Structure

The `backend/template.yaml` defines all serverless resources:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  # Environment-specific parameters

Globals:
  Function:
    Timeout: 300
    MemorySize: 128
    Runtime: python3.11

Resources:
  # Lambda functions, DynamoDB tables, S3 buckets, etc.

Outputs:
  # Stack outputs
```

## Adding a New Lambda Function

```yaml
NewFunctionFn:
  Type: AWS::Serverless::Function
  Properties:
    Description: Description of the function
    CodeUri: core/functions/new_function/src
    Handler: app.handler
    MemorySize: 256
    Timeout: 300
    Environment:
      Variables:
        TABLE_NAME: !Ref SomeTable
        BUCKET_NAME: !Ref SomeBucket
    Policies:
      - AWSLambdaBasicExecutionRole
      - Statement:
          - Effect: Allow
            Action:
              - dynamodb:GetItem
              - dynamodb:PutItem
            Resource: !GetAtt SomeTable.Arn
    Events:
      ApiGatewayPOST:
        Type: Api
        Properties:
          Path: /new-endpoint
          Method: POST
          RestApiId: !Ref ApiGateway
    Layers:
      - !Ref PortalProjectionLayer

NewFunctionFnLogGroup:
  Type: AWS::Logs::LogGroup
  DeletionPolicy: Retain
  UpdateReplacePolicy: Retain
  Properties:
    LogGroupName: !Sub /aws/lambda/${NewFunctionFn}
    RetentionInDays: 30
```

## Adding a Lambda Layer

```yaml
NewLayer:
  Type: AWS::Serverless::LayerVersion
  Properties:
    Description: Layer description
    ContentUri: core/layers/new_layer/src
    RetentionPolicy: Retain
  Metadata:
    BuildMethod: python3.11
```

## Adding a DynamoDB Table

```yaml
NewTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub ${AWS::StackName}-NewTable
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: id
        AttributeType: S
    KeySchema:
      - AttributeName: id
        KeyType: HASH
    PointInTimeRecoverySpecification:
      PointInTimeRecoveryEnabled: true
    SSESpecification:
      SSEEnabled: true
```

### Async Jobs Table (Existing)

The `AsyncJobsTable` is used for tracking long-running async validations (alien ID, military ID). It uses TTL to auto-expire jobs after 24 hours:

```yaml
AsyncJobsTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: !Sub ${AWS::StackName}-AsyncJobs
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: jobId
        AttributeType: S
    KeySchema:
      - AttributeName: jobId
        KeyType: HASH
    TimeToLiveSpecification:
      AttributeName: ttl
      Enabled: true
    PointInTimeRecoverySpecification:
      PointInTimeRecoveryEnabled: true
    SSESpecification:
      SSEEnabled: true
```

Both `KYCOrchestratorFn` and `DocumentValidationFn` need `DynamoDBCrudPolicy` for this table.

## Adding SSM Parameters

```yaml
# In template.yaml - grant access
Policies:
  - Statement:
      - Effect: Allow
        Action:
          - ssm:GetParameter
          - ssm:GetParameters
        Resource:
          - !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/jubilee/kyc/*

# Create parameters via CLI or console
aws ssm put-parameter \
  --name "/jubilee/kyc/feature-flags/face-matching-enabled" \
  --value "true" \
  --type "String"
```

## Deployment Commands

```bash
# Validate template
sam validate --lint

# Build artifacts
sam build

# Deploy with guided prompts (first time)
sam deploy --guided

# Deploy with existing config
sam deploy

# Deploy to specific environment
sam deploy --config-env production

# Deploy with parameter overrides
sam deploy --parameter-overrides \
  AmplifyS3BucketName=my-bucket \
  AmplifyCognitoUserPoolId=eu-west-1_xxxxx
```

## samconfig.toml

```toml
version = 0.1

[default.deploy.parameters]
stack_name = "jubilee-ekyc-backend"
resolve_s3 = true
s3_prefix = "jubilee-ekyc-backend"
region = "eu-west-1"
confirm_changeset = true
capabilities = "CAPABILITY_IAM CAPABILITY_AUTO_EXPAND"

[production.deploy.parameters]
stack_name = "jubilee-ekyc-backend-prod"
parameter_overrides = "AmplifyS3BucketName=prod-bucket"
```

## Local Testing

```bash
# Start local API
sam local start-api

# Invoke function locally
sam local invoke FunctionName -e events/test.json

# Generate sample event
sam local generate-event apigateway aws-proxy > events/test.json
```

## Troubleshooting

### Build Failures
```bash
# Clean build
rm -rf .aws-sam
sam build

# Build specific function
sam build FunctionName
```

### Deployment Failures
```bash
# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name jubilee-ekyc-backend

# Delete failed stack
sam delete --stack-name jubilee-ekyc-backend
```
