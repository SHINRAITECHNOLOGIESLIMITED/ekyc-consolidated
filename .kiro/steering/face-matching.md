---
inclusion: fileMatch
fileMatchPattern: "**/face_liveness/**,**/face_matching*"
---

# Face Matching Guidelines

This steering file is automatically included when working with face matching functionality.

## AWS Rekognition Integration

Face matching uses AWS Rekognition's `compare_faces` API.

### Basic Usage
```python
import boto3

rekognition = boto3.client('rekognition')

response = rekognition.compare_faces(
    SourceImage={'Bytes': source_image_bytes},
    TargetImage={'Bytes': target_image_bytes},
    SimilarityThreshold=70.0  # Required threshold
)
```

### Response Structure
```python
{
    'FaceMatches': [
        {
            'Similarity': 98.5,  # Percentage match
            'Face': {
                'BoundingBox': {...},
                'Confidence': 99.9
            }
        }
    ],
    'UnmatchedFaces': [...],
    'SourceImageFace': {...}
}
```

## 3-Way Face Comparison

The face matching feature requires comparing three photos:
1. **Customer Selfie** - Live photo from face liveness check
2. **Document Photo** - Photo extracted from ID document
3. **IPRS Photo** - Photo retrieved from IPRS database

### Comparison Matrix
| Comparison | Source | Target | Required |
|------------|--------|--------|----------|
| Selfie vs Document | Customer selfie | ID document photo | Yes |
| Selfie vs IPRS | Customer selfie | IPRS photo | Yes |
| Document vs IPRS | ID document photo | IPRS photo | Optional |

### Threshold Requirements
- Minimum similarity: **70%**
- All required comparisons must pass
- Overall result is `MATCH` only if all pass

## Image Handling

### Supported Formats
- JPEG, PNG for direct bytes
- Base64 encoded images (decode before use)
- S3 references for large images

### Image Quality
- Minimum resolution: 80x80 pixels
- Maximum size: 5MB per image
- Face must be clearly visible

## Error Scenarios

- `NO_FACE_DETECTED` - No face found in image
- `MULTIPLE_FACES` - More than one face in image
- `LOW_QUALITY` - Image quality too poor for comparison
- `THRESHOLD_NOT_MET` - Similarity below 70%
