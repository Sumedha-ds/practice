#!/usr/bin/env python3
"""
Test script for voice choice recognition endpoint
Tests the POST /api/auth/user-choice/recognize endpoint
"""

import requests
import os
import sys

# API base URL
BASE_URL = "http://localhost:5000"

def test_voice_choice():
    """Test the voice choice recognition endpoint"""
    
    print("=" * 60)
    print("Testing Voice Choice Recognition Endpoint")
    print("=" * 60)
    
    # Step 1: Verify OTP to get token
    print("\n1. Verifying OTP to get authentication token...")
    phone_number = input("Enter phone number (or press Enter for '9876543210'): ").strip()
    if not phone_number:
        phone_number = "9876543210"
    
    otp = input("Enter OTP (any 6 digits): ").strip()
    if not otp:
        otp = "123456"
    
    verify_response = requests.post(
        f"{BASE_URL}/api/auth/verify-otp",
        json={
            "phone_number": phone_number,
            "otp": otp
        }
    )
    
    if verify_response.status_code != 200:
        print(f"❌ OTP verification failed: {verify_response.json()}")
        return
    
    verify_data = verify_response.json()
    token = verify_data.get('token')
    print(f"✅ OTP verified! Token: {token[:20]}...")
    
    # Step 2: Get user choice question (optional - just to see the flow)
    print("\n2. Getting user choice question...")
    question_response = requests.get(
        f"{BASE_URL}/api/auth/user-choice/question",
        headers={"Authorization": f"Bearer {token}"},
        params={"language": "en"}
    )
    
    if question_response.status_code == 200:
        question_data = question_response.json()
        print(f"✅ Question: {question_data.get('question_text')}")
        print(f"   Audio base64 length: {len(question_data.get('audio_base64', ''))} chars")
    
    # Step 3: Test voice recognition with audio file
    print("\n3. Testing voice recognition with audio file...")
    print("   Looking for test audio files...")
    
    # Look for audio files in the project
    audio_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.wav', '.mp3', '.flac', '.aiff')):
                audio_files.append(os.path.join(root, file))
    
    if not audio_files:
        print("❌ No audio files found in the project.")
        print("   Please provide an audio file path, or we'll create a test request.")
        audio_path = input("Enter path to audio file (or press Enter to skip): ").strip()
        if not audio_path or not os.path.exists(audio_path):
            print("⚠️  Skipping audio file test. You can test manually with Postman.")
            return
    else:
        print(f"   Found {len(audio_files)} audio file(s):")
        for i, af in enumerate(audio_files[:5], 1):
            print(f"   {i}. {af}")
        
        choice = input(f"\n   Select audio file (1-{min(len(audio_files), 5)}) or enter custom path: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= min(len(audio_files), 5):
            audio_path = audio_files[int(choice) - 1]
        else:
            audio_path = choice if choice else audio_files[0]
    
    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    print(f"   Using audio file: {audio_path}")
    
    # Prepare multipart form data
    with open(audio_path, 'rb') as audio_file:
        files = {
            'audio': (os.path.basename(audio_path), audio_file, 'audio/wav')
        }
        data = {
            'language': 'en-US'
        }
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        print("   Sending audio file to backend...")
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/user-choice/recognize",
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            
            print(f"\n   Response Status: {response.status_code}")
            result = response.json()
            print(f"   Response: {result}")
            
            if response.status_code == 200:
                print(f"\n✅ Success!")
                print(f"   User Choice: {result.get('user_choice')}")
                print(f"   Recognized Text: {result.get('recognized_text')}")
                print(f"   Phone Number: {result.get('phone_number')}")
            else:
                print(f"\n❌ Error: {result.get('message')}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")

def test_with_text_alternative():
    """Test using the text-based endpoint as alternative"""
    print("\n" + "=" * 60)
    print("Alternative: Testing with text input (no audio file needed)")
    print("=" * 60)
    
    phone_number = input("\nEnter phone number (or press Enter for '9876543210'): ").strip()
    if not phone_number:
        phone_number = "9876543210"
    
    otp = input("Enter OTP (any 6 digits): ").strip()
    if not otp:
        otp = "123456"
    
    verify_response = requests.post(
        f"{BASE_URL}/api/auth/verify-otp",
        json={"phone_number": phone_number, "otp": otp}
    )
    
    if verify_response.status_code != 200:
        print(f"❌ OTP verification failed: {verify_response.json()}")
        return
    
    token = verify_response.json().get('token')
    print(f"✅ Token obtained: {token[:20]}...")
    
    voice_text = input("\nEnter your choice text (e.g., 'apply job', 'post job', 'learning module'): ").strip()
    if not voice_text:
        voice_text = "apply job"
    
    response = requests.post(
        f"{BASE_URL}/api/auth/user-choice",
        headers={"Authorization": f"Bearer {token}"},
        json={"voice_text": voice_text}
    )
    
    result = response.json()
    print(f"\nResponse: {result}")
    
    if response.status_code == 200:
        print(f"✅ User choice saved: {result.get('user_choice')}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Voice Choice Recognition Test")
    print("=" * 60)
    print("\nMake sure the API server is running on http://localhost:5000")
    print("Start it with: python api_server.py")
    
    choice = input("\nTest option:\n1. Test with audio file (requires audio file)\n2. Test with text input (no audio needed)\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        test_with_text_alternative()
    else:
        test_voice_choice()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

