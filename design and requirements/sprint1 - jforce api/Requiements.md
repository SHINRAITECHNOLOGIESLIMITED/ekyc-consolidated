# Identity Verification System

This system is designed to facilitate the secure and accurate identity verification of two primary user groups:

1.  **Agents:** Individuals or companies utilizing the system for the sales and onboarding of customers.
2.  **End Customers:** Individuals being signed up and onboarded by the agents.

The core function of the system is to collect essential personal data and supporting documents to confirm the legitimacy of the identity being provided for both agents and customers.

## Processes

### Agent Registration:

This process outlines the information and verification steps required for individuals or companies to register as agents within the system.

#### Agent Fields Captured:

* **AgentCode:** A unique alphanumeric identifier automatically assigned to the agent upon successful registration.
* **Name:** The full legal name of the agent (either the individual's name or the registered company name).
* **PIN Number:** The agent's Kenya Revenue Authority (KRA) Personal Identification Number.
* **ID No:** The agent's National Identification Card number (for individuals).

#### Agent Documents Captured:

* **Passport Photo:** A recent, clear passport-sized photograph of the individual agent or a representative for a company.
* **National ID Card:** A scanned copy of the agent's valid National Identification Card (for individuals).
* **Company Certificate of Registration:** A scanned copy of the official certificate of registration (for companies).

#### Agent Verification Process:

The verification process for agents involves a series of automated and potentially manual checks to confirm the accuracy and legitimacy of the provided information and documents:

1.  **Validation of Uploaded Documents:**
    * The system performs checks to verify that the uploaded ID/Passport document is authentic and the number matches the document itself.
    * The full name provided during registration is cross-referenced against the name present on the uploaded National ID Card or Company Certificate of Registration to ensure consistency.

2.  **Verification against External Services (ESB Services):**
    * The provided ID Number (for individuals) is verified against government identity databases to confirm its existence and validity.
    * The Name provided is cross-referenced with the name associated with the verified ID Number in the government identity database.
    * The KRA PIN Number is validated against the KRA tax database to confirm its existence and active status.
    * The ID Number associated with the agent is checked against the KRA tax database to ensure it matches the records linked to the provided PIN Number.
    * **For company agents**, verification include checking the company's registration status and details against  business registration database via ESB services


3.  **Background Checks:**
    * For individual agents, background checks are conducted using the provided Full Names and Date of Birth.

### Customer Onboarding:

This process outlines the information and verification steps required for onboarding new customers into the system.

#### Customer Fields Collected:

* **Name:** Full legal name of the customer.
* **PIN Number:** Customer's Kenya Revenue Authority (KRA) Personal Identification Number.
* **ID No/Passport No:** The customer's National Identification Card number or Passport number.
* **Gender:** Customer's gender (Male or Female).
* **Date Of Birth:** Customer's date of birth.
* **Customer Policy Beneficiaries:** Details of individuals designated as beneficiaries for any associated policies or services.

#### Customer Documents Captured:

* **Passport Photo:** A recent, clear passport-sized photograph of the customer.
* **National ID or Passport:** A scanned copy of the customer's valid National Identification Card or Passport (only one is required).
* **KRA PIN Card:** A scanned copy of the customer's KRA PIN certificate or document displaying the PIN.

#### Customer Policy Beneficiaries Fields Collected:

* **ID Number/Birth Certificate/Passport Number:** The primary identification number for the beneficiary (could be National ID, Birth Certificate number for minors, or Passport number).
* **Relationship:** The relationship of the beneficiary to the main customer (e.g., Spouse, Child, Parent, Sibling).
* **Gender:** The gender of the beneficiary.
* **Date Of Birth:** The date of birth of the beneficiary.

#### WIP Customer Verification Process:

The verification process for customers involves validating the provided information and documents:

1.  **Validation of Uploaded Documents:**
    * The system validates the uploaded National ID or Passport document confirming that the ID/Passport number matches the document.
    * The uploaded KRA PIN Card is validated to ensure the PIN number matches the provided one.
    * The customer's full name and Date of Birth provided during onboarding are cross-referenced with the details present on the uploaded National ID or Passport to ensure consistency.
    * The name on the uploaded KRA PIN Card is matched against the customer's provided name.

2.  **Verification against External Services (ESB Services):**
    * The provided Customer ID Number or Passport Number is verified against the relevant government identity database to confirm the customer's identity and the validity of the document.
    * Customer's Name, Gender, and Date of Birth are cross-referenced with the information associated with the verified ID/Passport Number in the government identity database.
    * The provided KRA PIN Number is validated against the KRA tax database to confirm its existence and active status.
    * The ID/Passport Number associated with the customer is checked against the KRA tax database to ensure it matches the records linked to the provided PIN Number.

3.  **Beneficiary Verification:**
    * For each listed beneficiary, the provided identification number (ID Number, Birth Certificate number, or Passport Number) is validated against relevant governement databases to confirm their existence.
    * The Name, Gender, and Date of Birth of each beneficiary are cross-referenced against available external government services depending on the type of identification provided (e.g., Birth Certificate verification).

4**Background Checks:**
    * Background checks are conducted using the provided Full Names and Date of Birth and attached to the registration