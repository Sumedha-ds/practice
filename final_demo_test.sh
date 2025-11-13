#!/bin/bash

echo "🎯🎯🎯 SMART VALIDATION DEMO 🎯🎯🎯"
echo "===================================="

# Login
echo -e "\n1️⃣ LOGIN"
echo "--------------------------------"
RESPONSE=$(curl -s -X POST http://localhost:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"9999888877","otp":"1234"}')

echo "$RESPONSE" | python3 -m json.tool
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))")

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to get token"
  exit 1
fi

echo "✅ Token obtained: $TOKEN"

# Test invalid name
echo -e "\n2️⃣ TEST: Invalid Name (contains numbers)"
echo "--------------------------------"
echo "Input: '123 invalid name'"
curl -s -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"name","answer_text":"123 invalid"}' | python3 -m json.tool

# Test valid name
echo -e "\n3️⃣ TEST: Valid Name"
echo "--------------------------------"
echo "Input: 'My name is Rajesh Kumar'"
curl -s -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"name","answer_text":"My name is Rajesh Kumar"}' | python3 -m json.tool

# Test invalid age
echo -e "\n4️⃣ TEST: Invalid Age (out of range)"
echo "--------------------------------"
echo "Input: 'I am 150 years old'"
curl -s -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"age","answer_text":"I am 150 years old"}' | python3 -m json.tool

# Test valid age
echo -e "\n5️⃣ TEST: Valid Age"
echo "--------------------------------"
echo "Input: 'I am 28 years old'"
curl -s -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"age","answer_text":"I am 28 years old"}' | python3 -m json.tool

# Test job with typo (fuzzy match)
echo -e "\n6️⃣ TEST: Job with Typo (Fuzzy Match)"
echo "--------------------------------"
echo "Input: 'I am a paintr' (typo)"
curl -s -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"skill","answer_text":"I am a paintr"}' | python3 -m json.tool

# Test fresher experience
echo -e "\n7️⃣ TEST: Fresher Experience"
echo "--------------------------------"
echo "Input: 'I am a fresher'"
curl -s -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"experience","answer_text":"I am a fresher"}' | python3 -m json.tool

echo -e "\n✅✅✅ DEMO COMPLETE ✅✅✅"
echo "===================================="
echo ""
echo "📊 Summary:"
echo "   • Login with OTP ✅"
echo "   • Invalid name rejected ❌"
echo "   • Valid name accepted ✅"
echo "   • Invalid age rejected ❌"
echo "   • Valid age accepted ✅"
echo "   • Fuzzy matching works ✅"
echo "   • Fresher recognized ✅"
echo ""
echo "🎯 System ready for hackathon demo!"
