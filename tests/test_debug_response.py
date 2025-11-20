#!/usr/bin/env python3
"""
Debug test to see raw API response structure.
"""

import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import requests

# Load .env file
load_dotenv()

def main():
    api_key = os.getenv('FIDOO_API') or os.getenv('FIDOO_API_KEY')
    base_url = os.getenv('FIDOO_BASE_URL') or os.getenv('FIDOO_API_URL')

    if not api_key:
        print("ERROR: Set FIDOO_API in .env file")
        sys.exit(1)

    # Create session
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "X-Api-Key": api_key,
    })

    # Test endpoints
    endpoints = [
        "user/get-users",
        "card/get-cards",
    ]

    for endpoint in endpoints:
        url = f"{base_url.rstrip('/')}/{endpoint}"
        print(f"\n{'='*60}")
        print(f"Endpoint: {endpoint}")
        print(f"URL: {url}")
        print(f"{'='*60}")

        response = session.post(url, json={"limit": 10})
        print(f"Status: {response.status_code}")

        try:
            data = response.json()
            print(f"\nResponse type: {type(data).__name__}")

            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"  {key}: list with {len(value)} items")
                    elif isinstance(value, dict):
                        print(f"  {key}: dict with keys {list(value.keys())[:5]}")
                    else:
                        print(f"  {key}: {type(value).__name__} = {str(value)[:50]}")
            elif isinstance(data, list):
                print(f"Array with {len(data)} items")

            print(f"\nFull response (first 500 chars):")
            print(json.dumps(data, indent=2, default=str)[:500])

        except Exception as e:
            print(f"Error parsing response: {e}")
            print(f"Raw response: {response.text[:500]}")

if __name__ == '__main__':
    main()
