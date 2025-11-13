#!/bin/bash
# Test script for voice choice recognition with audio file upload

BASE_URL="http://localhost:5000"
echo "=========================================="
echo "Testing Voice Choice Recognition"
echo "=========================================="

# Step 1: Verify OTP to get token
echo ""
echo "Step 1: Verifying OTP..."
VERIFY_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "9876543210", "otp": "1234"}')

echo "Response: $VERIFY_RESPONSE"
TOKEN=$(echo $VERIFY_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to get token"
  exit 1
fi

echo "✅ Token obtained: ${TOKEN:0:30}..."
echo ""

# Step 2: Get user choice question
echo "Step 2: Getting user choice question..."
QUESTION_RESPONSE=$(curl -s -X GET "$BASE_URL/api/auth/user-choice/question?language=en" \
  -H "Authorization: Bearer $TOKEN")

echo "Question Response: $QUESTION_RESPONSE"
echo ""

# Step 3: Test with audio file (if available)
echo "Step 3: Testing voice recognition with audio file..."
AUDIO_FILE=$(find audio -name "*.mp3" -o -name "*.wav" | head -1)

if [ -z "$AUDIO_FILE" ]; then
  echo "⚠️  No audio file found. Testing with text input instead..."
  
  # Test with text input
  TEXT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/user-choice" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"voice_text": "I want to apply for job"}')
  
  echo "Text Input Response: $TEXT_RESPONSE"
else
  echo "Using audio file: $AUDIO_FILE"
  
  # Note: MP3 files may not work directly with speech_recognition
  # We need WAV format. Let's try anyway and show the error if it fails
  AUDIO_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/user-choice/recognize" \
    -H "Authorization: Bearer $TOKEN" \
    -F "audio=@$AUDIO_FILE" \
    -F "language=en-US")
  
  echo "Audio Upload Response: $AUDIO_RESPONSE"
fi

echo ""
echo "=========================================="
echo "Test completed!"
echo "=========================================="

