# KYC Processing Results Portal

## Project Description

This project is a web portal built with Next.js and AWS Amplify Gen2 to display the results of Know Your Customer (KYC) processing. It provides a user interface to view, manage, and potentially initiate KYC workflows and access related documents and liveness detection results.

## Project Structure

The project follows a standard Next.js application structure with dedicated directories for Amplify configurations, public assets, source code, and build-related files.## Setup and Installation
```
.
├── amplify
├── amplify_outputs.json
├── download_amplify_outputs.sh
├── node_modules
├── package.json
├── public
├── README.md
└── src
```

To set up the project locally, follow these steps:

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd kyc-processing-results-portal
    ```

2.  **Install dependencies:**

    ```bash
    npm install
    ```

3.  **Configure AWS Amplify Gen2:**

    This project relies on AWS Amplify Gen2 for backend services. Deploy the project from AWS amplify console.

4.  **Download Amplify Outputs:**

    The project needs the `amplify_outputs.json` file to configure the Amplify client in the frontend. Run the provided script:

    ```bash
    ./download_amplify_outputs.sh
    ```

    * **Note:** You might need to make the script executable: `chmod +x ./download_amplify_outputs.sh`

5.  **Environment Variables:**

    Create a `.env.local` file in the project root for local environment variables. You might need to configure variables related to your AWS setup or API endpoints here. Consult your backend configuration for required variables.

    ```env
    # Example:
    # NEXT_PUBLIC_AWS_REGION=your-aws-region
    # NEXT_PUBLIC_USER_POOL_ID=your-user-pool-id
    # NEXT_PUBLIC_USER_POOL_CLIENT_ID=your-user-pool-client-id
    # NEXT_PUBLIC_API_ENDPOINT=your-api-endpoint
    ```
## Running the Project

To run the project locally in development mode:

```bash
npm run dev
```
## Deployment

This project is designed to be deployed on AWS Amplify Hosting:
AWS Amplify Hosting is configured to automatically deploy code changes pushed to the main branch of your connected repository.