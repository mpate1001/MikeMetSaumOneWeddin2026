#!/usr/bin/env python3
"""Quick test script for USPS OAuth - trying multiple variations"""
import os
import base64
import requests

consumer_key = os.environ.get('USPS_CONSUMER_KEY', '')
consumer_secret = os.environ.get('USPS_CONSUMER_SECRET', '')

if not consumer_key or not consumer_secret:
    print("ERROR: Set USPS_CONSUMER_KEY and USPS_CONSUMER_SECRET environment variables")
    exit(1)

print(f"Consumer Key: {consumer_key[:8]}...{consumer_key[-4:]}")
print(f"Consumer Secret: {consumer_secret[:4]}...{consumer_secret[-4:]}")

credentials = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()

# Test configurations to try
tests = [
    {
        "name": "Body params with scope (apis.usps.com)",
        "url": "https://apis.usps.com/oauth2/v3/token",
        "data": {
            "grant_type": "client_credentials",
            "client_id": consumer_key,
            "client_secret": consumer_secret,
            "scope": "addresses",
        },
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
    },
    {
        "name": "Body params without scope (apis.usps.com)",
        "url": "https://apis.usps.com/oauth2/v3/token",
        "data": {
            "grant_type": "client_credentials",
            "client_id": consumer_key,
            "client_secret": consumer_secret,
        },
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
    },
    {
        "name": "Basic Auth with scope (apis.usps.com)",
        "url": "https://apis.usps.com/oauth2/v3/token",
        "data": {
            "grant_type": "client_credentials",
            "scope": "addresses",
        },
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {credentials}",
        },
    },
    {
        "name": "Basic Auth without scope (apis.usps.com)",
        "url": "https://apis.usps.com/oauth2/v3/token",
        "data": {"grant_type": "client_credentials"},
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {credentials}",
        },
    },
    {
        "name": "Body params with scope (api.usps.com - no s)",
        "url": "https://api.usps.com/oauth2/v3/token",
        "data": {
            "grant_type": "client_credentials",
            "client_id": consumer_key,
            "client_secret": consumer_secret,
            "scope": "addresses",
        },
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
    },
]

for test in tests:
    print(f"\n--- {test['name']} ---")
    try:
        response = requests.post(
            test["url"],
            data=test["data"],
            headers=test["headers"],
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:300]}")

        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token', '')
            print(f"\n✅ SUCCESS! Got access token: {token[:30]}...")

            # Test the address API
            print("\n--- Testing Address API ---")
            test_response = requests.get(
                'https://apis.usps.com/addresses/v3/address',
                params={
                    'streetAddress': '1600 Pennsylvania Ave NW',
                    'city': 'Washington',
                    'state': 'DC',
                    'ZIPCode': '20500',
                },
                headers={
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/json',
                },
                timeout=10
            )
            print(f"Address API Status: {test_response.status_code}")
            print(f"Address API Response: {test_response.text[:400]}")
            break  # Stop on first success
    except Exception as e:
        print(f"Error: {e}")
