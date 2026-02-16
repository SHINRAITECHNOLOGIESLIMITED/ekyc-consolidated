# Release Notes for 0.1.0

## Release Date: 2025-06-20

# Release Notes

## Breaking Changes
_No breaking changes were identified in this release._

---

## Features

- **Agent & Registration Enhancements**
  - Improved agent details UI and adjusted the liveness threshold.
  - Improved agent type branching, enhanced query language usage in registration, traceability, and introduced a state machine for the agent registration process.
  - Updated default agent type to 'Business' and made the ID Number field required for individual agent forms.
  - Enhanced traceability of agent registration.

- **KYC Certificates & Document Management**
  - Added KYC certificate preview on the customer details page.
  - Improved naming conventions of certificate files and expanded agent data for certificates.
  - Implemented PDF KYC certificate generation and S3 uploads for customers.
  - Added a Lambda skeleton for KYC certificate generation.
  - Added customer KYC certificate generation capability.
  - Improved certificate registration and validation flows for business agents.
  - Implemented secure API for streaming documents directly from S3 using presigned URLs and Next.js image optimizations.
  - Added a new document streaming API with deployment and configuration enhancements.
  - Added automated deletion of all Lambda log groups with a verbose option for easier management.
  - Improved customer details presentation and allowed document access on those pages.
  - Enhanced support for path-based routing and input validation in the certification flow.
  - Enabled doc access from the customer details page.

- **Liveness Detection & Face Liveness**
  - Improved face liveness status display and standardized state machine updates.
  - Added confidence threshold display and lowered the liveness detection threshold for better sensitivity.
  - Added new model fields and refined the liveness detection UI.
  - Enforced schema validation and added a liveness session details page.
  - Improved liveness detection UX, lowered detection thresholds, and introduced expiry time to sessions.
  - Enhanced error handling and S3 storage in face liveness and background check flows.
  - Added policy for backend Rekognition liveness and improved related error handling.
  - Enabled AWS Rekognition FaceLiveness API access for users.
  - Added error handling to the FaceLivenessDetector UI component.
  - Introduced a new action to capture and manage liveness checks.
  - Improved the Face Liveness Sessions navigation experience.

- **API & Developer Tools**
  - Added Cognito integration to API gateway and enhanced stage configuration.
  - Updated API authorizer examples to include AWS_IAM and Lambda.
  - Enhanced developer environment with multi-language support and updated development container settings.
  - Enhanced dev environment and removed unused dependencies.
  - Added an example .env file for easier script configuration.
  - Added support for capturing new liveness checks directly from the interface.
  - Added schema validation error handling and clarified test utilities.

- **Dashboard & UX Improvements**
  - Enhanced dashboard metrics layout, improved performance panel styling, and removed deprecated dependencies.
  - Improved DocumentForm UX, submission state management, and error handling.

---

## Bug Fixes

- Updated CORS headers to explicitly allow GET methods and removed unused configurations.
- Improved API error handling, especially for cached API calls and government verification, with clearer messaging.
- Enhanced error handling and messaging in the background check and generic API flows.
- Fixed issue with making the ID Number optional in the background check form.
- Improved API response handling and logging for cached calls.

---

## Improvements

- **Refactoring & Code Quality**
  - Streamlined deployment and API configuration for document streaming functionality.
  - Improved readability, logging, and error handling across multiple modules, including agent registration and certification.
  - Migrated customer registration to template-based input and streamlined retry logic.
  - Simplified codebase by removing unused lambdas, dependencies, and portal update operations during certificate creation.
  - Improved environment variable management for S3 uploads.
  - Cleaned up and clarified test case naming.
  - Enhanced backend error handling and logging; cleaned up utilities and standardized error responses.
  - Updated DynamoDB table settings for face liveness operations.
  - Renamed document verification column from 'accuracy' to 'validity' and fixed related naming in code.
  - Changed model naming for document responses to improve clarity.

- **UI Enhancements**
  - Updated navigation and removed "Work in Progress" badge for Face Liveness Sessions to reflect production readiness.
  - Improved system performance panel styling in the interface.

---

## Documentation

- Added example .env file for developer and deployment configuration.
- Updated authorizer examples in API gateway documentation to clarify usage of AWS_IAM and Lambda.

---

## Chore & Other

- Bumped application version numbers at each release milestone for version tracking.
- Cleaned up unused dependencies across development and portal environments.
- Improved logging and test utility functions for better backend observability.
- Pulled in release and merge branches to maintain a consistent development baseline.

---

_Thank you to all contributors and users for your continued feedback and support!_

---

*These release notes were automatically generated from commit history.*