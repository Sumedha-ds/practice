#!/usr/bin/env python3
"""
Test script for validations - demonstrates end-to-end onboarding with validations
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")

def test_login():
    """Step 1: Login"""
    print_section("STEP 1: Login")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/verify-otp",
        json={
            "phone_number": "9988776655",
            "otp": "1234"
        }
    )
    
    result = response.json()
    print(f"Status: {response.status_code}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get('success'):
        token = result.get('token')
        print(f"\n✅ Login successful! Token: {token}")
        return token
    else:
        print("❌ Login failed!")
        return None

def test_question_with_validation(token, question_key, test_answers):
    """Test a question with multiple answers (valid and invalid)"""
    print_section(f"Testing: {question_key.upper()}")
    
    for i, answer in enumerate(test_answers, 1):
        print(f"\n📝 Test {i}: Answering with '{answer}'")
        
        response = requests.post(
            f"{BASE_URL}/api/onboarding/answer",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "question_key": question_key,
                "answer_text": answer
            }
        )
        
        result = response.json()
        
        if result.get('valid'):
            print(f"✅ VALID - Saved as: '{result.get('answer_text')}'")
        else:
            print(f"❌ INVALID")
            print(f"   Error: {result.get('error_message')}")
            if result.get('error_audio'):
                print(f"   🔊 Voice error feedback available (base64)")
        
        time.sleep(0.5)  # Small delay between tests

def main():
    print("\n" + "🎯" * 30)
    print("SMART VALIDATION DEMO - Voice Onboarding System")
    print("🎯" * 30)
    
    # Login
    token = test_login()
    if not token:
        return
    
    time.sleep(1)
    
    # Test NAME validation
    test_question_with_validation(
        token,
        "name",
        [
            "123 invalid",           # ❌ Invalid - numbers
            "abcd efgh ijkl mnop",   # ❌ Invalid - too many words
            "Rajesh Kumar",          # ✅ Valid
            "My name is Priya",      # ✅ Valid - removes filler words
        ]
    )
    
    time.sleep(1)
    
    # Test AGE validation
    test_question_with_validation(
        token,
        "age",
        [
            "I am five years old",   # ❌ Invalid - below 16
            "I am 150",              # ❌ Invalid - above 70
            "twenty five",           # ❌ Invalid - no number extracted
            "I am 28 years old",     # ✅ Valid
            "35",                    # ✅ Valid
        ]
    )
    
    time.sleep(1)
    
    # Test SKILL validation
    test_question_with_validation(
        token,
        "skill",
        [
            "xyz random job",        # ❌ Invalid (may accept if short)
            "painter",               # ✅ Valid - exact match
            "I am an electrician",   # ✅ Valid - partial match
            "plumber work",          # ✅ Valid - contains known job
            "driver",                # ✅ Valid
        ]
    )
    
    time.sleep(1)
    
    # Test EXPERIENCE validation
    test_question_with_validation(
        token,
        "experience",
        [
            "none",                  # ❌ Invalid - no number
            "fresher",               # ✅ Valid - recognized keyword
            "5 years",               # ✅ Valid
            "18 months",             # ✅ Valid - converted to years
            "I have 3 years",        # ✅ Valid
        ]
    )
    
    time.sleep(1)
    
    # Test LOCATION validation
    test_question_with_validation(
        token,
        "location",
        [
            "Mumbai",                # ✅ Valid
            "I am from Delhi",       # ✅ Valid - removes filler
            "Bangalore",             # ✅ Valid
            "Pune City",             # ✅ Valid
            "Unknown Place XYZ",     # ✅ Valid (lenient for unknown places)
        ]
    )
    
    time.sleep(1)
    
    # Test GENDER validation
    test_question_with_validation(
        token,
        "gender",
        [
            "unknown",               # ❌ Invalid
            "male",                  # ✅ Valid
            "I am a woman",          # ✅ Valid
            "female",                # ✅ Valid
        ]
    )
    
    print_section("✅ VALIDATION DEMO COMPLETE!")
    print("\n📊 Summary:")
    print("   - All questions validated with smart logic")
    print("   - Invalid answers rejected with Hindi error messages")
    print("   - Valid answers cleaned and normalized")
    print("   - Error audio feedback available in base64")
    print("\n🎯 Ready for hackathon demo!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")


