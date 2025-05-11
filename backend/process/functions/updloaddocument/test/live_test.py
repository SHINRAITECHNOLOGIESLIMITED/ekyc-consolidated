#!/usr/bin/env python3
import requests
import json
base_url = "https://sfl7nouy94.execute-api.eu-west-1.amazonaws.com/Prod"
endpoint = f"{base_url}/uploaddocument"
auth_token = "eyJraWQiOiJYZEhqT3pJRzV6T0U5YTRTeGNwNWFvRmVMUFpJdWFEdU1FNE4yWm1FOExVPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJjMmE1ZTQ2NC0zMGIxLTcwZTgtZWViMC04YzE5NmRhODgxNDciLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLmV1LXdlc3QtMS5hbWF6b25hd3MuY29tXC9ldS13ZXN0LTFfZU1OSURGc3h4IiwiY29nbml0bzp1c2VybmFtZSI6ImMyYTVlNDY0LTMwYjEtNzBlOC1lZWIwLThjMTk2ZGE4ODE0NyIsIm9yaWdpbl9qdGkiOiI3Yjg0NjRmMS02YjNiLTQxMDktODg1OC05YjRlYTJlNWJiODYiLCJhdWQiOiI1a2hhOTRnMHV0NWh2M2lzazNrbGZnY29ybCIsImV2ZW50X2lkIjoiNmVjNzFlZDQtNmMwMS00M2YxLWExNDAtMWQ4YTQ4ZGFiMmI2IiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3NDY4NTk5MDcsImV4cCI6MTc0Njg3NjM1NCwiaWF0IjoxNzQ2ODcyNzU0LCJqdGkiOiJkNGEzZTcxZS0yYTBkLTRhMjctOWJmNS1hMWM0NTIzYzAwM2UiLCJlbWFpbCI6InN0ZXZlLmJpa29Ac2hpbnJhaXRlY2hub2xvZ2llcy5pbyJ9.fWUQmQMvepH4-KYl2AW0vmyiebdrnPnudGRRClWl627idILL7NPdJ6we3AYyPnRKu3RxA6CQUgiTkRYwQ18LATA2dyishFKTpKngN2RwD9C-VillJ1drdD_lwB57UIiewZVSklOB1ouCvu-hXh1-HW3XxVyD9oAS8sQwsn1Nadxfi6j1tqVlOb0dZpDRZ1bYQZ1nU1xLsOY-3n2KB_0NGy3Z0MhQKRj5GcmzFLIURpuy7Y3ijab9dZwtE_YqT2wPOahW3k6YF87xL8YdbuzWJ2wgMbqUK0ubZFPVOEIb7318lus9Eu3HoahJCnUzADQ7ZBVH_zTv2pzKK2bkKNtNjw"

# Payload for the POST request
payload = {"documentType":"KENYAN_NATIONAL_ID",
           "customerId":"12345",
           "s3Path":"protected/eu-west-1:c2a5e464-30b1-70e8-eeb0-8c196da88147/12345/KENYAN_NATIONAL_ID-2f0807618052c5aab1de9e230093e060550f9029.jpeg"}
headers  = {
    'Content-Type': 'application/json',
    'Authorization': auth_token,
    'Origin':'https://main.d2896e60a8d7f8.amplifyapp.com'
}

def pre_flight():
    
    print("=" * 80)
    print("MAKING OPTIONS REQUEST (PREFLIGHT)")
    print("=" * 80)
    
    # Make OPTIONS request (preflight)
    options_response = requests.options(endpoint, headers=headers)
    
    print(f"Status Code: {options_response.status_code}")
    print("\nResponse Headers:")
    for header, value in options_response.headers.items():
        print(f"{header}: {value}")

def post():
    print("\n" + "=" * 80)
    print("MAKING POST REQUEST")
    print("=" * 80)
    
    # Make POST request with authorization
    post_response = requests.post(
        endpoint,
        headers=headers,
        json=payload
    )
    
    print(f"Status Code: {post_response.status_code}")
    print("\nResponse Headers:")
    for header, value in post_response.headers.items():
        print(f"{header}: {value}")
    
    print("\nResponse Body:")
    try:
        print(json.dumps(post_response.json(), indent=2))
    except:
        print(post_response.text)

if __name__ == "__main__":
    # pre_flight()
    post()