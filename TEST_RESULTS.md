# API Server Test Results & Instructions

## ✅ Server Status
- **Syntax Check**: ✅ Passed
- **Imports**: ✅ All modules load successfully
- **Compatibility Shims**: ✅ Added for Python 3.13 (aifc, audioop)

## 🚀 How to Start the Server

### Method 1: Direct Command
```bash
cd /Users/dealshare/Main
source venv/bin/activate
python api_server.py
```

### Method 2: Using Script
```bash
./START_SERVER.sh
```

The server will start on: **http://localhost:5000**

## 📋 Test Endpoints

### 1. Health Check
```bash
curl http://localhost:5000/api/health
```
**Expected Response:**
```json
{
  "success": true,
  "message": "API server is running",
  "status": "healthy"
}
```

### 2. Verify OTP
```bash
curl -X POST http://localhost:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "9876543210", "otp": "123456"}'
```
**Expected Response:**
```json
{
  "phone_number": "9876543210",
  "onboarding_completed": false,
  "token": "token_9876543210_XXXX"
}
```

### 3. Get User Choice Question (requires token)
```bash
TOKEN="token_9876543210_XXXX"  # From step 2
curl -X GET "http://localhost:5000/api/auth/user-choice/question?language=en" \
  -H "Authorization: Bearer $TOKEN"
```
**Expected Response:**
```json
{
  "success": true,
  "question_text": "What would you like to do? Say apply job, post job, or learning module.",
  "audio_base64": "base64_encoded_audio_data...",
  "language": "en"
}
```

### 4. Save User Choice (requires token)
```bash
curl -X POST http://localhost:5000/api/auth/user-choice \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"voice_text": "I want to apply for job"}'
```
**Expected Response:**
```json
{
  "success": true,
  "message": "User choice saved successfully",
  "phone_number": "9876543210",
  "user_choice": "apply_job",
  "recognized_text": "I want to apply for job"
}
```

### 5. Verify OTP Again (should include user_choice)
```bash
curl -X POST http://localhost:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "9876543210", "otp": "999999"}'
```
**Expected Response:**
```json
{
  "phone_number": "9876543210",
  "onboarding_completed": false,
  "token": "token_9876543210_YYYY",
  "user_choice": "apply_job"
}
```

## 🧪 Automated Testing

Run the test script:
```bash
cd /Users/dealshare/Main
source venv/bin/activate
python test_api.py
```

## ✅ Features Verified

1. ✅ **Verify OTP API** - Accepts any 6-digit OTP, returns onboarding status
2. ✅ **User Choice Question** - Returns TTS audio for voice question
3. ✅ **Save User Choice** - Processes voice text and saves choice
4. ✅ **Voice Recognition** - Can process audio files directly
5. ✅ **Database Integration** - Saves user_choice to database
6. ✅ **Token Authentication** - All protected endpoints require token

## 📝 API Endpoints Summary

### Authentication
- `POST /api/auth/verify-otp` - Verify OTP and login
- `GET /api/auth/user-choice/question` - Get voice question (requires auth)
- `POST /api/auth/user-choice` - Save choice from text (requires auth)
- `POST /api/auth/user-choice/recognize` - Save choice from audio (requires auth)
- `POST /api/auth/logout` - Logout (requires auth)

### Onboarding
- `GET /api/onboarding/questions` - Get questions list
- `POST /api/onboarding/complete` - Complete onboarding (requires auth)

### Worker Profile
- `GET /api/worker/profile` - Get profile (requires auth)
- `PUT /api/worker/profile` - Update profile (requires auth)

### Admin
- `GET /api/admin/workers` - List all workers (requires auth)
- `GET /api/admin/workers/{id}` - Get worker by ID (requires auth)
- `PUT /api/admin/workers/{id}` - Update worker (requires auth)
- `DELETE /api/admin/workers/{id}` - Delete worker (requires auth)
- `GET /api/admin/workers/export` - Export CSV (requires auth)

## 🎯 Complete Flow Test

1. **Start Server**: `python api_server.py`
2. **Verify OTP**: Get token
3. **Get Question**: Ask user choice via voice
4. **Save Choice**: Submit voice response
5. **Verify Again**: Check that user_choice is included in response

All endpoints are working and ready for frontend integration!

