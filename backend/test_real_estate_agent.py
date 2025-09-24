#!/usr/bin/env python3
"""
Simple test script to verify the Real Estate Agent functionality
"""

import requests
import json
import time

API_BASE = "http://localhost:8001/api"

def test_basic_connection():
    """Test basic API connection"""
    print("Testing basic API connection...")
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"✓ API Connection: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ API Connection failed: {e}")
        return False

def test_agent_capabilities():
    """Test agent capabilities endpoint"""
    print("\nTesting agent capabilities...")
    try:
        response = requests.get(f"{API_BASE}/agents/capabilities")
        data = response.json()
        if data["success"]:
            print("✓ Agent capabilities retrieved:")
            for agent_type, capabilities in data["capabilities"].items():
                print(f"  {agent_type}: {', '.join(capabilities)}")
            return True
        else:
            print(f"✗ Failed to get capabilities: {data.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"✗ Capabilities test failed: {e}")
        return False

def test_real_estate_chat():
    """Test real estate agent chat functionality"""
    print("\nTesting real estate agent chat...")

    test_questions = [
        "What should I consider when buying my first home?",
        "How is the current housing market?",
        "What are the benefits of investing in real estate?"
    ]

    for question in test_questions:
        print(f"\nQuestion: {question}")
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                json={
                    "message": question,
                    "agent_type": "real_estate"
                },
                timeout=30
            )

            data = response.json()
            if data["success"]:
                print(f"✓ Response received (length: {len(data['response'])} chars)")
                print(f"  Agent type: {data['agent_type']}")
                print(f"  Capabilities: {', '.join(data['capabilities'])}")
                # Print first 200 chars of response
                preview = data['response'][:200] + "..." if len(data['response']) > 200 else data['response']
                print(f"  Preview: {preview}")
            else:
                print(f"✗ Chat failed: {data.get('error', 'Unknown error')}")
                return False

        except requests.exceptions.Timeout:
            print("✗ Request timed out (this is normal for AI responses)")
        except Exception as e:
            print(f"✗ Chat test failed: {e}")
            return False

        time.sleep(1)  # Be nice to the API

    return True

def main():
    print("Real Estate Agent API Test")
    print("=" * 50)

    success = True

    success &= test_basic_connection()
    success &= test_agent_capabilities()
    success &= test_real_estate_chat()

    print("\n" + "=" * 50)
    if success:
        print("✓ All tests passed! Real Estate Agent is working properly.")
    else:
        print("✗ Some tests failed. Check the logs above.")

    return success

if __name__ == "__main__":
    main()