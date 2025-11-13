#!/bin/bash

echo "🧪 Quick Validation Test"
echo "========================"

# Login
echo -e "\n1️⃣ Login..."
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"9988776655","otp":"1234"}' | \
  grep -o '"token":"[^"]*' | cut -d'"' -f4)

echo "Token: $TOKEN"

# Test invalid name
echo -e "\n2️⃣ Test INVALID name (123 invalid)..."
curl -s -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"name","answer_text":"123 invalid"}' | python3 -m json.tool

# Test valid name
echo -e "\n3️⃣ Test VALID name (Rajesh Kumar)..."
curl -s -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"name","answer_text":"My name is Rajesh Kumar"}' | python3 -m json.tool

# Test invalid age
echo -e "\n4️⃣ Test INVALID age (150)..."
curl -s -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"age","answer_text":"I am 150 years old"}' | python3 -m json.tool

# Test valid age
echo -e "\n5️⃣ Test VALID age (28)..."
curl -s -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"age","answer_text":"I am 28 years old"}' | python3 -m json.tool

echo -e "\n✅ Tests complete!"
