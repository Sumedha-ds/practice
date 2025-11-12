#!/usr/bin/env python3
"""Test script for API endpoints"""
import sys
import json

# Add compatibility shims
import types
try:
    import aifc
except ModuleNotFoundError:
    aifc_module = types.ModuleType('aifc')
    aifc_module.Error = Exception
    aifc_module.open = lambda *args, **kwargs: None
    sys.modules['aifc'] = aifc_module

try:
    import audioop
except ModuleNotFoundError:
    try:
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
    except ImportError:
        pass

import requests

BASE_URL = "http://localhost:5000/api"

def test_health():
    """Test health check endpoint"""
    print("\n1. Testing Health Check...")
    try:
        r = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {r.status_code}")
        print(f"   Response: {json.dumps(r.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_verify_otp():
    """Test verify OTP endpoint"""
    print("\n2. Testing Verify OTP...")
    try:
        data = {
            "phone_number": "9876543210",
            "otp": "123456"
        }
        r = requests.post(f"{BASE_URL}/auth/verify-otp", json=data)
        print(f"   Status: {r.status_code}")
        response = r.json()
        print(f"   Response: {json.dumps(response, indent=2)}")
        
        if 'token' in response:
            return response['token']
        return None
    except Exception as e:
        print(f"   Error: {e}")
        return None

def test_user_choice_question(token):
    """Test get user choice question"""
    print("\n3. Testing Get User Choice Question...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/auth/user-choice/question?language=en", headers=headers)
        print(f"   Status: {r.status_code}")
        response = r.json()
        print(f"   Question Text: {response.get('question_text', 'N/A')}")
        print(f"   Audio Base64: {'Present' if response.get('audio_base64') else 'Missing'}")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_save_user_choice(token):
    """Test save user choice"""
    print("\n4. Testing Save User Choice...")
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        data = {
            "voice_text": "I want to apply for job"
        }
        r = requests.post(f"{BASE_URL}/auth/user-choice", json=data, headers=headers)
        print(f"   Status: {r.status_code}")
        response = r.json()
        print(f"   Response: {json.dumps(response, indent=2)}")
        return response.get('user_choice')
    except Exception as e:
        print(f"   Error: {e}")
        return None

def test_verify_otp_again():
    """Test verify OTP again to see if user_choice is included"""
    print("\n5. Testing Verify OTP Again (should include user_choice)...")
    try:
        data = {
            "phone_number": "9876543210",
            "otp": "999999"
        }
        r = requests.post(f"{BASE_URL}/auth/verify-otp", json=data)
        print(f"   Status: {r.status_code}")
        response = r.json()
        print(f"   Response: {json.dumps(response, indent=2)}")
        return True
    except Exception as e:
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("API Server Test Suite")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Server is not running. Please start it first:")
        print("   cd /Users/dealshare/Main && source venv/bin/activate && python api_server.py")
        sys.exit(1)
    
    # Test 2: Verify OTP
    token = test_verify_otp()
    if not token:
        print("\n❌ Failed to get token")
        sys.exit(1)
    
    # Test 3: Get user choice question
    test_user_choice_question(token)
    
    # Test 4: Save user choice
    choice = test_save_user_choice(token)
    if choice:
        print(f"\n✓ User choice saved: {choice}")
    
    # Test 5: Verify OTP again (should include user_choice)
    test_verify_otp_again()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

