# Jubilee eKYC Backend

This project utilizes the AWS Serverless Application Model (SAM) to deploy several serverless applications composed of Python-based Lambda functions. The project is organized into logical modules (`core` and `process`), each containing its own set of Lambda functions and potentially state machines. Shared libraries are located in the `shared` directory.

## Project Structure
```
├── core
│ ├── functions
│ └── state_machines
├── __init__.py
├── process
│ ├── functions
│ └── state_machines
├── README.md
├── samconfig.toml
├── shared
│ └── libraries
└── template.yaml
```
## Prerequisites

Before you begin, ensure you have the following installed:

* **AWS CLI:** [Install the AWS Command Line Interface](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
* **AWS SAM CLI:** [Install the AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
* **Python 3.11:** Ensure you have Python 3 installed on your system.
* **pip:** Python package installer (usually comes with Python).
* **Docker:** Required for local testing of Lambda functions that rely on specific build environments or have external dependencies. [Install Docker](https://docs.docker.com/get-docker/)

## Building the Project

The SAM CLI provides commands to build your serverless application. This step prepares your Python code and dependencies for deployment.

1.  **Navigate to the project root directory** in your terminal.

2.  **Build the SAM application:**

    ```bash
    sam build
    ```

    This command will automatically discover the function definitions in your `template.yaml` file and build the necessary artifacts, including installing Python dependencies defined in `requirements.txt` files within each function's `src` directory. The built artifacts will be placed in a `.aws-sam` directory.

    You can also build specific functions if needed:

    ```bash
    sam build jubilee_esb_call updloaddocument
    ```

## Local Testing with SAM Local

The SAM CLI allows you to run and debug your Lambda functions locally, for development and testing.

### Running Lambda Functions Locally

You can invoke your Lambda functions locally using the `sam local invoke` command.

1.  **Ensure your application is built** using `sam build`.

2.  **Invoke a specific Lambda function:**

    ```bash
    sam local invoke IprsidentityverificationFunction -e core/functions/jubilee_esb_call/test/events/event.json
    ```

    * Replace `IprsidentityverificationFunction` with the logical ID of the Lambda function defined in your `template.yaml`.
    * Replace `core/functions/iprsidentityverification/test/events/event.json` with the path to a JSON file containing the event data you want to pass to the function. You'll need to create these event files within the `test/events` directories of your Lambda functions.

    For functions that interact with other AWS services, you might need to mock those services or configure your local environment accordingly.

### Running a Local API Gateway

If your SAM application includes an API Gateway, you can simulate it locally using `sam local start-api`.

1.  **Ensure your application is built** using `sam build`.

2.  **Start the local API Gateway:**

    ```bash
    sam local start-api
    ```

    This command will start a local HTTP server that mimics the behavior of API Gateway. You can then send HTTP requests to the endpoints defined in your `template.yaml`. The output will show the local URL where your API is running (usually `http://localhost:3000`).

    You can then test your API endpoints using tools like `curl`, Postman, or a web browser. For example, if you have a GET endpoint defined for the `iprsidentityverification` function under a certain path, you might access it like this:

    ```bash
    curl http://localhost:3000/your/api/path
    ```

### Running Step Functions Locally

If your SAM application includes AWS Step Functions state machines, you can execute them locally using `sam local start-state-machine` and `sam local execute-state-machine`.

1.  **Ensure your application is built** using `sam build`.

2.  **Start the local Step Functions endpoint:**

    ```bash
    sam local start-state-machine
    ```

    This will start a local endpoint for Step Functions.

3.  **Execute a specific state machine:**

    ```bash
    sam local execute-state-machine --resource-id YourStateMachineLogicalId --event events/state_machine_event.json
    ```

    * Replace `YourStateMachineLogicalId` with the logical ID of your state machine in `template.yaml`.
    * Replace `events/state_machine_event.json` with a JSON file containing the input for your state machine.

    You'll need to consult the SAM CLI documentation for more advanced local testing scenarios, such as debugging Lambda functions.

## Testing

Each Lambda function has a dedicated `test` directory containing unit tests. It is recommended to write comprehensive tests to ensure the reliability of your functions. You can use Python's built-in `unittest` framework or other testing frameworks like `pytest`.

To run the tests for a specific function, navigate to its `test` directory and execute your testing framework's command. For example, using `unittest`:

```bash
cd core/functions/jubilee_esb_call/test
python -m unittest discover .
```
## Deployment
### Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Update the .env file with your credentials:

- JUBILEE_ESB_CREDENTIALS: JSON string containing ESB API credentials
- PORTAL_GRAPHQL_CREDENTIALS: JSON string containing Portal GraphQL credentials

3. Before deploying, load the environment variables:
```bash
source .env
```
### Deployment scripts
```bash
sam validate --lint #to ensure sam template is valid
sam build #to prepare the artifacts
sam deploy #to deploy to aws region as per parameters configure in the environment
```

## Cleanup

To delete the application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
sam delete --stack-name "jubilee-ekyc-backend"
```

## Resources

See the [AWS SAM developer guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html) for an introduction to SAM specification, the SAM CLI, and serverless application concepts.