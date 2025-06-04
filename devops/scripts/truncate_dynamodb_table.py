#!/usr/bin/env python3
import boto3
from botocore.exceptions import ClientError
from tqdm import tqdm
MAGIC_CHOICE = 1984
MAGIC_CHOICE_NAME = "*ALL*"
            
session = boto3.Session(profile_name='shinrai.devpost')
dynamodb_client = session.client('dynamodb')

def getDynamoDBTables():
    response = dynamodb_client.list_tables()
    table_names = response['TableNames']
    return [t for t in table_names if 'jubileeapicache' not in t.lower()]


def getUserTruncateConfirmation(tablename):
    while True:
        response = input(f"Do you want to truncate all items in {tablename} default=yes? (yes/no)/(y/n): ").lower().strip()
        if response == 'yes' or response == 'y' or response == '':
            return 1
        elif response == 'no' or response == 'n':
            return None
        else:
            print("Please answer with 'yes' or 'no'.")


def getUserDeleteTableChoise(table_names):
    print("Select a table to truncate:")
    print("0. Cancel")
    for i, table_name in enumerate(table_names):
        print(f"{i + 1}. {table_name}")
    while True:
        try:
            choice = int(input("Enter the number of the table to truncate: "))
            if choice == 0:
                return None
            if 1 <= choice <= len(table_names):
                return table_names[choice - 1]
            elif choice == MAGIC_CHOICE:
                return MAGIC_CHOICE_NAME
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def get_table_keys(table_name):
    """Get the primary key attributes for the table"""
    try:
        response = dynamodb_client.describe_table(TableName=table_name)
        key_schema = response['Table']['KeySchema']
        return [key['AttributeName'] for key in key_schema]
    except ClientError as e:
        print(f"Error getting table keys: {e.response['Error']['Message']}")
        raise


def truncateDynamoDBTable(table_name):
    # Create a session with the specified profile

    BATCH_SIZE = 25
    try:
        key_attributes = get_table_keys(table_name)
        print(f"Table keys: {key_attributes}")
        LastEvaluatedKey = None
        deleted = 0
        while True:
            if LastEvaluatedKey:
                scan_response = dynamodb_client.scan(
                    TableName=table_name,
                    ExclusiveStartKey=scan_response['LastEvaluatedKey']
                )
            else:
                scan_response = dynamodb_client.scan(TableName=table_name)

            items = scan_response['Items']

            for i in tqdm(range(0, len(items), BATCH_SIZE)):
                batch_items = items[i:i + BATCH_SIZE]
                request_items = {
                    table_name: [
                        {
                            'DeleteRequest': {
                                'Key': {
                                    k: v for k, v in item.items() if k in key_attributes
                                }
                            }
                        } for item in batch_items
                    ]
                }

                if batch_items:
                    # print(f"Deleting {len(batch_items)} items...")
                    dynamodb_client.batch_write_item(RequestItems=request_items)
                    deleted += len(batch_items)
            if 'LastEvaluatedKey' in scan_response:
                LastEvaluatedKey = scan_response['LastEvaluatedKey']
            else:
                break
        print(f"Deleted {deleted} items from {table_name}")
    except ClientError as e:
        print(f"Error truncating table: {e.response['Error']['Message']}")
        raise


if __name__ == '__main__':
    

    # 1. query dynamodb table names
    table_names = getDynamoDBTables()

    # 2. choose a table to truncate
    table_name = getUserDeleteTableChoise(table_names)
    if table_name is None:
        print("Operation cancelled.")
    elif table_name:
        # 3. ask user to confirm truncation
        choice = getUserTruncateConfirmation(tablename=table_name)
        if choice is None:
            print("Operation cancelled.")
        elif choice  and table_name == MAGIC_CHOICE_NAME:
            for table_name2 in table_names:
                truncateDynamoDBTable(table_name2)    
        else:  # truncate
            print(f"Deleting all items from {table_name}...")
            truncateDynamoDBTable(table_name)