# API Endpoints Summary

This document summarizes the API endpoints for the Identity Verification System, designed to handle the registration and verification of agents and customers.

## Endpoints

* **POST /agent-registration**
    * **Summary:** Registers a new agent (individual or company) in the system.
    * **Description:** Accepts agent details and document URLs to initiate the agent onboarding process, including specifying whether the agent is an individual or a company.

* **POST /customer-registration**
    * **Summary:** Registers a new customer in the system.
    * **Description:** Collects customer personal details, document URLs, and beneficiary information for the customer onboarding process.

* **POST /government/nationalid-verification**
    * **Summary:** Verifies National ID details against a government identity database.
    * **Description:** Takes an individual's National ID Number, Full Names, and Date of Birth to confirm their existence and verify the accuracy of the provided information with the relevant government authority.

* **POST /government/passport-verification**
    * **Summary:** Verifies Passport details against a government database.
    * **Description:** Takes an individual's Passport Number, Full Names, and Date of Birth to confirm their existence and verify the accuracy of the provided information with the relevant government authority.

* **POST /government/kra-verification**
    * **Summary:** Verifies KRA PIN details against the KRA database.
    * **Description:** Takes a KRA PIN, associated Full Names, and linked ID Number (National ID or Passport) to confirm the validity and active status of the PIN and its association with the provided identity.

* **POST /government/company-verification**
    * **Summary:** Verifies Company details against a government business registration database.
    * **Description:** Takes a Business Registration Number and the Registered Company Name to confirm the registration status and details of the company with the relevant government authority.

* **POST /document/nationalid-validation**
    * **Summary:** Validates details extracted from an uploaded National ID document.
    * **Description:** Processes an uploaded National ID document image (via URL), extracts key data points, and compares them against user-provided National ID Number, Full Names, and Date of Birth to validate the document's authenticity and data consistency.

* **POST /document/passport-validation**
    * **Summary:** Validates details extracted from an uploaded Passport document.
    * **Description:** Processes an uploaded Passport document image (via URL), extracts key data points, and compares them against user-provided Passport Number, Full Names, and Date of Birth to validate the document's authenticity and data consistency.

* **POST /document/kra-validation**
    * **Summary:** Validates details extracted from an uploaded KRA PIN document.
    * **Description:** Processes an uploaded KRA PIN document image (via URL), extracts key data points, and compares them against user-provided KRA PIN, Full Names, and linked ID Number to validate the document's authenticity and data consistency.

* **POST /document/company-validation**
    * **Summary:** Validates details extracted from an uploaded Company Certificate of Registration document.
    * **Description:** Processes an uploaded Company Certificate of Registration image (via URL), extracts key data points (like registration number and company name), and compares them against user-provided Business Number and Registered Company Name to validate the document's authenticity and data consistency.