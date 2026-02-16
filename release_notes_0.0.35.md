# Release Notes for 0.0.35

## Release Date: 2025-05-10

# Release Notes

## Breaking Changes
_No breaking changes were introduced in this release._

---

## Features

- **AI-Powered Release Notes and Enhanced Logging**  
  Introduced automated, AI-driven release notes generation, robust logging mechanisms, and a user-friendly UI for improved release workflows.

- **AI-Powered Commit Messages Configuration**  
  Added options for user configuration and logging specifically for AI-generated commit messages, enhancing flexibility and transparency.

- **Automated Release Script**  
  Developed an automated release script to streamline version management.

- **Cognito Authorization for API**  
  Integrated Cognito User Pool authorization to API endpoints, enhancing security.

- **Event Schema Validation and Simplified Handlers**  
  Implemented comprehensive event schema validation and simplified handler logic for increased reliability.

- **Improved Step Function Outputs and Status Checks**  
  Enhanced Step Functions to produce more informative outputs and enable granular status monitoring.

- **Robust Document Registration Workflow**  
  Introduced a comprehensive state machine workflow for document registration, supporting more robust processing.

- **VBDM Git Integration**  
  Enhanced the VBDM workflow with automated git fetch and pull steps before running the AWS SAM process.

- **Script for Stopping Step Functions Executions**  
  Added a utility script to halt ongoing AWS Step Functions executions easily.

- **Per-Document Details Page**  
  Added a dedicated details page for each document, accessible via the listing page for deeper insights.

- **Document Status & UI Enhancements**  
  Enabled status updates for documents and improved data visibility within the user interface.

- **Improved Portal Integration and API Observability**  
  Refactored the portal integration and enhanced the observability of API calls.

- **S3 Path and Enhanced Portal API Configuration**  
  Replaced document URLs with an S3 path implementation and improved configuration options for the portal API.

- **Dynamic API Authorization**  
  Implemented dynamic authentication headers and flexible token handling for API requests.

---

## Bug Fixes

- **Navigation Title Version Rendering**  
  Ensured the application version number is always correctly rendered as a string in the navigation title.

---

## Improvements

- **Standardized Step Function Workflows**  
  Standardized JSON path usage and simplified state machine workflows for more maintainable state management.

- **Removed Unused IAM Roles**  
  Cleaned up template files by removing unused IAM role resources for Step Functions.

- **Step Function Extraction Refactor**  
  Migrated document extraction invocation logic to utilize Step Functions, aligning with overall workflow enhancements.

---

## Documentation

_No documentation-specific updates in this release._

---

## Chore & Other

- **Version Bumps**  
  Updated project versioning to v0.0.31, v0.0.32, v0.0.33, and v0.0.34 as part of the release process.
  
- **General Maintenance**  
  Routine project maintenance tasks performed to ensure build stability and up-to-date dependencies.

---

**Thank you for using our software!**  
_For further details, please refer to the individual commit history._

---

*These release notes were automatically generated from commit history.*