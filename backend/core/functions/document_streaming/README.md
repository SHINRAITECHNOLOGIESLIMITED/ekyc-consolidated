# Document Streaming API

This API allows direct streaming of documents from S3 buckets through API Gateway.

## Usage

Access documents using the following URL pattern:

```
GET /stream/{bucketType}/{documentKey}
```

Where:
- `bucketType` is one of: `kyc`, `liveness`, or `certification`
- `documentKey` is the S3 key of the document

## Examples

```
# Access a KYC document
GET /stream/kyc/path/to/document.pdf

# Access a face liveness capture
GET /stream/liveness/session123/image.jpg

# Access a certification document
GET /stream/certification/individual_agents_ekyc_certificates/12345/agent_20230101123456_certificate.pdf
```

## Response

The API returns the document directly with the appropriate Content-Type header.

## Error Responses

- `400 Bad Request`: Missing or invalid parameters
- `404 Not Found`: Document does not exist
- `500 Internal Server Error`: Server-side error

## Security

- Access to this API should be restricted using appropriate authentication and authorization
- All document access is logged for audit purposes