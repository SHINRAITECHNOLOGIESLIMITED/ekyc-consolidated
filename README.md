# Jubilee eKYC
Serverless electronic Know Your Customer (eKYC) solution on AWS for Jubilee Insurance Company
## Overview

This platform automates and enhances the KYC process by allowing customers to upload their identification documents and perform a face liveness check. The backend, built as an AWS SAM application, extracts crucial information from uploaded documents using AWS Textract. This extracted data undergoes validation against proprietary APIs, including IPRS (Integrated Population Registration System), KRA (Kenya Revenue Authority), and LexisNexis, ensuring the authenticity and accuracy of the submitted information.

In addition to document verification, the backend provides an endpoint for face liveness detection using AWS Rekognition. This module analyzes user-submitted video or image sequences to determine if the person is physically present and not a spoof. The results of both the document verification and liveness checks are stored in a DynamoDB database. Upon successful verification, a digital KYC certificate summarizing the results is generated and stored in an S3 bucket.

The frontend portal, an AWS Amplify Gen 2 project, provides a user interface for customers to interact with the backend APIs. Data within the portal is managed using AppSync.

## Repository Structure

```
├── backend
├── design and requirements
├── devops
├── portal
├── README.md
└── requirements-dev.txt
```

## Backend

The `backend` directory contains the AWS Serverless Application Model (SAM) project responsible for the core KYC document processing and face liveness detection logic.

### Functionality

-   **KYC Document Processing API:** Provides an API endpoint for receiving and processing uploaded KYC documents.
    -   **Document Extraction:** Leverages AWS Textract to extract structured JSON data from various KYC document formats.
    -   **Robust Data Validation:** Integrates with proprietary APIs of IPRS, KRA, and LexisNexis to validate the extracted customer information against official records.
    -   **Data Storage:** Persists processed customer records and verification statuses in DynamoDB.
    -   **KYC Certification:** Generates a digital KYC certification document upon successful verification and stores it securely in Amazon S3.
-   **Face Liveness Detection API:** Provides an API endpoint for performing face liveness checks.
    -   Utilizes AWS Rekognition to analyze user-submitted video or image sequences.
    -   Stores session results and a competence score (indicating the likelihood of a live person) in DynamoDB.

### Technology Stack

-   AWS SAM
-   Python
-   AWS Lambda
-   AWS Textract
-   AWS Rekognition
-   Amazon DynamoDB
-   Amazon S3
-   Integration with IPRS, KRA, and LexisNexis APIs

### Deployment
#### Backend Deployment
Deployment instructions for the backend service can be found in `backend/README.md`. 
This will  involve using the AWS SAM CLI to package and deploy the CloudFormation stack defined in `template.yaml`. 

** Requirement **
- Ensure you have the AWS CLI and SAM CLI installed and configured with appropriate AWS credentials.
- Ensure python enviroment is initialized and dependencies in requirements-dev.txt installed using:
```bash
pip install -r requirements-dev.txt
```

#### FrontEnd Deployment
Deployment instructions for setting up, configuring, and deploying the frontend portal can be found in `portal/README.md`. 
This will involve using the AWS Amplify CLI and ensuring it is properly configured for your AWS environment.


## Design and Requirements

The `design and requirements` directory contains documentation outlining the project's specifications and architecture.

-   `Design.xlsx`: Contains detailed design specifications.
-   `eKYC-F-Proposed-ekyc-architecture.drawio.png`: A visual diagram illustrating the proposed architecture of the eKYC system.
-   `IPRS_LEXISNEXIS_KRA API DOC.pdf`: Documentation for the integrated proprietary APIs (IPRS, KRA, and LexisNexis) used for data validation.
-   `sample-kyc-documents`: A collection of sample KYC documents used for development and testing purposes.
-   `Technical Proposal - AWS Serverless eKYC Architecture.pdf`: The initial technical proposal outlining the serverless architecture on AWS.

## DevOps

The `devops` directory contains documentation related to the development operations standards adopted for this project.

-   `Jubilee_eKYC_-_Shinrai_DevOps_Standards.docx`: Outlines the DevOps principles, practices, and tools to be used throughout the branching strategy, including CI/CD pipelines, infrastructure as code, monitoring, and logging strategies.

## Portal

The `portal` directory houses the source code for the web portal, built as an AWS Amplify Gen 2 project. This portal provides the user interface for interacting with the backend KYC processing and liveness detection APIs.

### Functionality

-   **Graphica; User Interface:** Offers a user-friendly interface for customers to securely upload their KYC documents and perform the face liveness check.
-   **Backend API Integration:** Integrates with the backend APIs to submit documents for processing and initiate liveness detection sessions.
-   **Browsing of Results:** Allows authenticated users to browse the status and results of KYC verification and liveness checks.

### Technology Stack
-  AWS SAM (Python + Yaml)
-  AWS Amplify Gen 2 (Next.js + React )

## Getting Started

To get started with this project, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Set up the backend:** Navigate to the `backend` directory and follow the instructions in `backend/README.md` to configure and deploy the AWS SAM application.

3.  **Set up the portal:** Navigate to the `portal` directory and follow the instructions in `portal/README.md` to install dependencies and configure the AWS Amplify Gen 2 project.

4.  **Review documentation:** Familiarize yourself with the design specifications, architecture diagram, and API documentation located in the `design and requirements` directory. Also, review the DevOps standards outlined in the `devops` directory.

### Contributing using Gitflow

How to contribute using the Gitflow workflow and the `git flow` command-line tool.

**1. Install Git Flow**

First, ensure you have Git installed. Then, install the Git Flow extension based on your operating system:

* **macOS (using Homebrew):**
    ```bash
    brew install git-flow-avh
    ```
* **Linux (Debian/Ubuntu):**
    ```bash
    sudo apt-get install git-flow
    ```
* **Windows:**
  Git for Windows now often includes Git Flow. You can check by opening your Git Bash or command prompt and typing `git flow version`. If it's not installed, you might need to download it separately or use a package manager like Chocolatey (`choco install git-flow`). Refer to the official Git Flow installation guides for detailed instructions if needed.

**2. Initialize Git Flow in your Repository**

If Git Flow hasn't been initialized in the repository, you'll need to do it once:

```bash
git flow init -d
```
The -d flag initializes with the default branch names (main for production, develop for development, feature/, release/, hotfix/ prefixes). You can omit -d if you want to customize these names.

**3. Ensure you have the latest develop branch:**

It's a good practice to start with an up-to-date develop branch.

```bash
git checkout develop
git pull origin develop
```

**4. Create a new feature branch:**

Use git flow feature start to create a new feature branch based on develop. Replace <feature-name> with a concise description of your feature (e.g., add-user-authentication).

```
git flow feature start <feature-name>
```

This command will create and switch you to a new branch named feature/<feature-name>.

**5. Develop your feature:**

Make your changes, commit them locally, and regularly push your work to your remote feature branch.

```bash
git add .
git commit -m "feat: Implement your new feature"
git push origin feature/<feature-name>
```

**6. Open a Pull Request (PR):**

Once your feature is complete and you're ready for review, create a pull request from your feature/<feature-name> branch to the develop branch on the main repository.

    1. Provide a clear and descriptive title for your PR.
    2. Explain the purpose of your feature and any relevant details.
    3. Reference any related issues or design documents.

**7. Code Review:**

Your pull request will be reviewed by other team members. Address any feedback and make necessary changes. Push the updated commits to your feature branch; the PR will automatically update.

**8. Finish the feature:**

Once your pull request is approved and merged (typically by a maintainer via the PR interface), you can use git flow feature finish to clean up locally.

```
git flow feature finish <feature-name>
```