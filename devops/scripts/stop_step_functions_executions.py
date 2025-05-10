import concurrent
import math
import multiprocessing
import sys
from concurrent.futures import ThreadPoolExecutor

import boto3
from tqdm import tqdm

"""
This script finds and stops all currently running executions for a specified AWS Step Functions State Machine.

It prompts the user for the AWS profile name, region name, and the State Machine ARN, providing default values.
It then connects to AWS Step Functions using the provided credentials and region.
The script lists running executions for the target State Machine in batches of up to 1000,
prioritizing the most recent ones.
It uses a thread pool to concurrently send stop requests for the found executions in chunks.
The process is repeated in a loop until no more running executions are found,
providing a progress bar and a total count of stopped executions.

Inputs:
- AWS Profile Name (string)
- AWS Region Name (string)
- AWS Step Functions State Machine ARN (string)

Outputs:
- Prints status messages to the console.
- Prints error messages to standard error and exits on failure (e.g., invalid input, AWS connection error, failure to stop an execution).
- Stops running AWS Step Functions executions.
"""

default_profile_name = 'shinrai.sandbox' #'default','shinrai.devpost'
default_region_name = 'eu-west-1'
default_state_machine_arn = 'arn:aws:states:eu-west-1:746147082282:stateMachine:NewDocumentRegistration-1j8IdTUEkm32'

# Prompt user for inputs, showing defaults
profile_input = input(f"Please enter the AWS profile name (default: {default_profile_name}): ")
region_input = input(f"Please enter the AWS region name (default: {default_region_name}): ")
state_machine_arn_input = input(f"Please enter the Step Functions State Machine ARN (default: {default_state_machine_arn}): ")

# Determine final values, using defaults if input was empty
profile_name = profile_input if profile_input else default_profile_name
region_name = region_input if region_input else default_region_name
state_machine_arn = state_machine_arn_input if state_machine_arn_input else default_state_machine_arn

# Validate inputs
if not profile_name:
    print("Error: Profile name cannot be empty.", file=sys.stderr)
    sys.exit(1)  # Exit with a non-zero status code to indicate an error

if not region_name:
    print("Error: Region name cannot be empty.", file=sys.stderr)
    sys.exit(1)

if not state_machine_arn:
    print("Error: State Machine ARN cannot be empty.", file=sys.stderr)
    sys.exit(1)

if not state_machine_arn.startswith("arn:aws:states:"):
    print("Error: Invalid State Machine ARN format.", file=sys.stderr)
    sys.exit(1)
try:
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    print(f"AWS Session created successfully for profile '{profile_name}' in region '{region_name}'.")

except Exception as e:
    print(f"Error creating AWS session: {e}", file=sys.stderr)
    print("Please ensure the profile name and region are correct and configured.", file=sys.stderr)
    sys.exit(1)

# Assign the validated ARN
state_machine_arn = state_machine_arn
print(f"State Machine ARN set to: {state_machine_arn}")

sf = session.client('stepfunctions')
BATCH_SIZE = 1000


def chunk_list(lst, chunk_size):
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def stop_execution(executions):
    """Helper function to stop a single execution"""
    success = 0
    for execution in executions:
        try:

            executionArn = execution['executionArn']
            sf.stop_execution(executionArn=executionArn)
            success += 1
        except Exception as err:
            print(f" Couldn't stop an execution due to the following error: {err=}")
            exit(1)
    return success


def process_chunk(chunk):
    """Process a chunk of executions"""
    results = []
    for execution in chunk:
        result = stop_execution(execution)
        results.append(result)
    return results


def find_stop():
    runningExecutions = sf.list_executions(
        stateMachineArn=state_machine_arn,
        statusFilter='RUNNING',
        maxResults=1000)
    executions = runningExecutions['executions']
    executions = sorted(executions, key=lambda x: x['startDate'], reverse=True)

    # pprint(executions)
    if not executions:
        pass
        # print("No running executions")
    else:
        if len(executions) > BATCH_SIZE:
            # print(f"\n{len(executions)} running executions found, only the {BATCH_SIZE} most recent will be stopped.\n")
            executions = executions[: BATCH_SIZE]
        else:
            # print(f"\n{len(executions)} running executions found\n")
            pass
        num_workers = max(2, multiprocessing.cpu_count() - 2)
        chunk_size = math.ceil(len(executions) / num_workers)
        chunks = chunk_list(executions, chunk_size)

        successful_stops = 0
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(stop_execution, chunk) for chunk in chunks]
            # Show progress bar for completed chunks
            with tqdm(total=len(chunks), desc="Processing chunks") as pbar:
                for future in concurrent.futures.as_completed(futures):
                    results = future.result()
                    successful_stops += results
                    pbar.update(1)
        # print(f"Successfully stopped {successful_stops} executions")
    return len(executions)


if __name__ == '__main__':
    all_stopped = 0
    while True:
        stopped = find_stop()
        all_stopped += stopped
        print(f"Total stopped executions: {all_stopped}")
        if stopped == 0:
            break
