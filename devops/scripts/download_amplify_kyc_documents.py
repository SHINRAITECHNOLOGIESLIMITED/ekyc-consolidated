#!/usr/bin/env python3
#download all documents from amplify kyc bucket
from pprint import pprint
import boto3    
import os
import pandas as pd

AMPLIFY_KYC_BUCKET = "amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq"
DESTINATION_FOLDER = "temp/amplify_kyc_documents"

session = boto3.Session(profile_name='shinrai.devpost')
s3 = session.client('s3')

def download_amplify_kyc_documents():
    downloaded_files = []
    # Ensure the destination folder exists
    if not os.path.exists(DESTINATION_FOLDER):
        os.makedirs(DESTINATION_FOLDER)
    
    # List objects in the S3 bucket
    response = s3.list_objects_v2(Bucket=AMPLIFY_KYC_BUCKET)
    
    if 'Contents' in response:
        for obj in response['Contents']:
            file_key = obj['Key']
            file_name = os.path.join(DESTINATION_FOLDER, file_key.split('/')[-1])
            
            # Download the file
            s3.download_file(AMPLIFY_KYC_BUCKET, file_key, file_name)
            # print(f"Downloaded {file_key} to {file_name}")
            file_record = dict(s3Key=file_key, file_name=file_name)
            downloaded_files.append(file_record)
            print("-" * 20)
            pprint(file_record)
    else:
        print("No files found in the bucket.")
    df = pd.DataFrame(downloaded_files)
    df.to_csv(os.path.join(DESTINATION_FOLDER, 'downloaded_files.csv'), index=False)
if __name__ == "__main__":
    download_amplify_kyc_documents()