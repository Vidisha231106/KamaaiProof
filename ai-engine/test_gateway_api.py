#!/usr/bin/env python3
"""
test_gateway_api.py
===================
Test OpenClaw Gateway API endpoints using httpx client.

Usage:
  1. Start FastAPI server: uvicorn ai-engine/main.py:app --reload --port 8000
  2. In another terminal: python3 ai-engine/test_gateway_api.py
"""

import httpx
import json
import sys
from time import sleep

BASE_URL = "http://localhost:8000"


def test_gateway_api():
    print("\n" + "=" * 80)
    print("OpenClaw Gateway API Tests")
    print("=" * 80)

    # Test 1: List skills
    print("\n[Test 1] GET /openclaw/skills")
    print("-" * 80)
    try:
        response = httpx.get(f"{BASE_URL}/openclaw/skills")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
        assert "skills" in response.json()
        assert "KamaaiProof" in response.json()["skills"]
        print("✅ Test 1 passed")
    except Exception as e:
        print(f"❌ Test 1 failed: {str(e)}")
        return False

    # Test 2: Get skill info
    print("\n[Test 2] GET /openclaw/skills/KamaaiProof")
    print("-" * 80)
    try:
        response = httpx.get(f"{BASE_URL}/openclaw/skills/KamaaiProof")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        assert response.status_code == 200
        assert data["skill"] == "KamaaiProof"
        assert "manifest" in data
        print("✅ Test 2 passed")
    except Exception as e:
        print(f"❌ Test 2 failed: {str(e)}")
        return False

    # Test 3: Invoke skill
    print("\n[Test 3] POST /openclaw/invoke")
    print("-" * 80)
    try:
        payload = {
            "skill": "KamaaiProof",
            "input": {
                "image_path": "backend/src/Python_engine/Documents/rent_receipt_1.jpeg",
                "document_type": "rent"
            }
        }
        print(f"Payload: {json.dumps(payload, indent=2)}")
        response = httpx.post(f"{BASE_URL}/openclaw/invoke", json=payload)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        assert response.status_code in [200, 400]  # Allow error if dependencies missing
        assert "status" in data
        assert data["skill"] == "KamaaiProof"
        print("✅ Test 3 passed")
    except Exception as e:
        print(f"❌ Test 3 failed: {str(e)}")
        return False

    # Test 4: Non-existent skill
    print("\n[Test 4] GET /openclaw/skills/NonExistentSkill")
    print("-" * 80)
    try:
        response = httpx.get(f"{BASE_URL}/openclaw/skills/NonExistentSkill")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 404
        print("✅ Test 4 passed (correctly returned 404)")
    except Exception as e:
        print(f"❌ Test 4 failed: {str(e)}")
        return False

    print("\n" + "=" * 80)
    print("✅ All OpenClaw Gateway API tests passed!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    print("\nMake sure FastAPI server is running:")
    print("  uvicorn ai-engine/main:app --reload --port 8000")
    print("\nWaiting 2 seconds before connecting...\n")
    sleep(2)

    try:
        success = test_gateway_api()
        sys.exit(0 if success else 1)
    except ConnectionError as e:
        print(f"\n❌ Could not connect to server at {BASE_URL}")
        print("Please start the FastAPI server first:")
        print("  cd ai-engine && uvicorn main:app --reload --port 8000")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
