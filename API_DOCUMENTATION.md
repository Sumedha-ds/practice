# API Documentation

This document lists all the API endpoints that need to be implemented for frontend integration.

## Base URL
```
http://localhost:5000/api  (or your server URL)
```

## Authentication
All endpoints (except login/OTP) should include authentication token in headers:
```
Authorization: Bearer <token>
```

---

## 1. Authentication & Login APIs

### 1.1 Verify OTP
**Endpoint:** `POST /auth/verify-otp`

**Description:** Verify OTP (accepts any 6-digit OTP) and check if onboarding is completed

**Request Body:**
```json
{
  "phone_number": "1234567890",
  "otp": "123456"
}
```

**Note:** Any 6-digit number is accepted as OTP (no validation against generated OTP)

**Response:**
```json
{
  "phone_number": "1234567890",
  "onboarding_completed": true,
  "token": "token_1234567890_1234",
  "user_choice": "apply_job"  // Optional: only included if user has already made a choice
}
```

**Response Fields:**
- `phone_number`: The phone number that was verified
- `onboarding_completed`: `true` if onboarding is completed, `false` if not
- `token`: Authentication token to use for subsequent API calls
- `user_choice`: (Optional) User's choice: `apply_job`, `post_job`, or `learning_module` - only included if user has previously made a choice

**Important:** After login, immediately call `/api/auth/user-choice/question` to ask user their choice via voice, regardless of onboarding status.

**Error Response:**
```json
{
  "success": false,
  "message": "Invalid phone number format"
}
```

---

### 1.2 Check Profile Status
**Endpoint:** `GET /auth/check-profile/{phone_number}`

**Description:** Check if profile exists for a phone number

**Response:**
```json
{
  "success": true,
  "phone_number": "1234567890",
  "profile_exists": true,
  "profile_created": 1
}
```

---

### 1.3 Get User Choice Question (Voice)
**Endpoint:** `GET /auth/user-choice/question`

**Description:** Get the question text and audio (TTS) for asking user's choice

**Query Parameters:**
- `language`: `en` or `hi` (default: `en`)

**Response:**
```json
{
  "success": true,
  "question_text": "What would you like to do? Say apply job, post job, or learning module.",
  "audio_base64": "base64_encoded_audio_data",
  "language": "en"
}
```

**Note:** The `audio_base64` can be decoded and played to ask the question via voice.

---

### 1.4 Save User Choice (Voice Text)
**Endpoint:** `POST /auth/user-choice`

**Description:** Save user's choice from voice response text

**Request Body:**
```json
{
  "voice_text": "I want to apply for job"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User choice saved successfully",
  "phone_number": "1234567890",
  "user_choice": "apply_job",
  "recognized_text": "I want to apply for job"
}
```

**Valid Choices:**
- `apply_job` - User wants to apply for jobs
- `post_job` - User wants to post a job
- `learning_module` - User wants to access learning module

**Error Response:**
```json
{
  "success": false,
  "message": "Could not understand your choice. Please say: apply job, post job, or learning module.",
  "recognized_text": "some text"
}
```

---

### 1.5 Recognize Voice Choice (Audio File)
**Endpoint:** `POST /auth/user-choice/recognize`

**Description:** Recognize voice input from audio file (multipart upload) and save user's choice

**Request:**
- Content-Type: `multipart/form-data`
- Field: `audio` (audio file - WAV, FLAC, AIFF)
- Field: `language` (optional, default: `en-US`)

**Frontend Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append('audio', audioBlob, 'recording.wav');
formData.append('language', 'en-US');

const response = await fetch('/api/auth/user-choice/recognize', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

**Response:**
```json
{
  "success": true,
  "user_choice": "apply_job",
  "recognized_text": "I want to apply for job",
  "phone_number": "1234567890"
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Could not understand audio. Please try again."
}
```

**Supported Audio Formats:**
- WAV (recommended)
- FLAC
- AIFF

---

### 1.6 Logout
**Endpoint:** `POST /auth/logout`

**Description:** Logout current user

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 2. Onboarding APIs

### 2.1 Get Onboarding Questions
**Endpoint:** `GET /onboarding/questions`

**Description:** Get list of onboarding questions

**Query Parameters:**
- `language`: `en` or `hi` (default: `en`)

**Response:**
```json
{
  "success": true,
  "questions": [
    {
      "key": "name",
      "en": "What is your name?",
      "hi": "आपका नाम क्या है?"
    },
    {
      "key": "skill",
      "en": "What is your skill? (eg: plumber, painter)",
      "hi": "आपका कौशल क्या है? (जैसे: पलंबर, पेंटर)"
    },
    {
      "key": "education",
      "en": "What is your education level?",
      "hi": "आपकी शिक्षा क्या है?"
    },
    {
      "key": "age",
      "en": "What is your age?",
      "hi": "आपकी उम्र क्या है?"
    },
    {
      "key": "sex",
      "en": "What is your sex? (male/female)",
      "hi": "आपका लिंग क्या है? (पुरुष/महिला)"
    },
    {
      "key": "experience",
      "en": "How many years of experience?",
      "hi": "अनुभव के वर्षों की संख्या क्या है?"
    },
    {
      "key": "location",
      "en": "Which city or village are you from?",
      "hi": "आप किस शहर या गांव से हैं?"
    },
    {
      "key": "wage_expected",
      "en": "What is your expected daily wage?",
      "hi": "आपकी अपेक्षित दैनिक मजदूरी क्या है?"
    },
    {
      "key": "languages_known",
      "en": "Which languages do you know?",
      "hi": "आप किन भाषाओं को जानते हैं?"
    }
  ]
}
```

---

### 2.2 Submit Onboarding Answer
**Endpoint:** `POST /onboarding/answer`

**Description:** Submit answer for a specific onboarding question

**Request Body:**
```json
{
  "phone_number": "1234567890",
  "question_key": "name",
  "answer": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Answer saved",
  "next_question": {
    "key": "skill",
    "en": "What is your skill?",
    "hi": "आपका कौशल क्या है?"
  }
}
```

---

### 2.3 Complete Onboarding
**Endpoint:** `POST /onboarding/complete`

**Description:** Complete onboarding and save profile

**Request Body:**
```json
{
  "phone_number": "1234567890",
  "answers": {
    "name": "John Doe",
    "skill": "Plumber",
    "education": "High School",
    "age": "30",
    "sex": "Male",
    "experience": "5",
    "location": "Mumbai",
    "wage_expected": "500",
    "languages_known": "Hindi English"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Onboarding complete and saved",
  "worker_id": 123,
  "phone_number": "1234567890"
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Phone number already exists. Please login instead."
}
```

---

## 3. Worker Profile APIs

### 3.1 Get Worker Profile
**Endpoint:** `GET /worker/profile`

**Description:** Get current logged-in worker's profile

**Response:**
```json
{
  "success": true,
  "profile": {
    "id": 123,
    "phone_number": "1234567890",
    "name": "John Doe",
    "skill": "Plumber",
    "education": "High School",
    "age": "30",
    "sex": "Male",
    "experience": "5",
    "location": "Mumbai",
    "aadhaar": "",
    "wage_expected": "500",
    "languages_known": "Hindi English",
    "profile_created": 1,
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

---

### 3.2 Update Worker Profile
**Endpoint:** `PUT /worker/profile`

**Description:** Update worker profile

**Request Body:**
```json
{
  "name": "John Doe Updated",
  "skill": "Electrician",
  "education": "Graduate",
  "age": "31",
  "sex": "Male",
  "experience": "6",
  "location": "Delhi",
  "wage_expected": "600",
  "languages_known": "Hindi English Kannada"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully"
}
```

---

## 4. Admin Dashboard APIs

### 4.1 Get All Workers
**Endpoint:** `GET /admin/workers`

**Description:** Get list of all workers (admin only)

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50)
- `search`: Search by name, phone, or skill

**Response:**
```json
{
  "success": true,
  "workers": [
    {
      "id": 123,
      "phone_number": "1234567890",
      "name": "John Doe",
      "skill": "Plumber",
      "education": "High School",
      "age": "30",
      "sex": "Male",
      "experience": "5",
      "location": "Mumbai",
      "aadhaar": "",
      "wage_expected": "500",
      "languages_known": "Hindi English",
      "profile_created": 1,
      "timestamp": "2024-01-15T10:30:00"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 50
}
```

---

### 4.2 Get Worker by ID
**Endpoint:** `GET /admin/workers/{worker_id}`

**Description:** Get specific worker details (admin only)

**Response:**
```json
{
  "success": true,
  "worker": {
    "id": 123,
    "phone_number": "1234567890",
    "name": "John Doe",
    "skill": "Plumber",
    "education": "High School",
    "age": "30",
    "sex": "Male",
    "experience": "5",
    "location": "Mumbai",
    "aadhaar": "",
    "wage_expected": "500",
    "languages_known": "Hindi English",
    "profile_created": 1,
    "timestamp": "2024-01-15T10:30:00",
    "raw_answers": "{\"name\":\"John Doe\",...}"
  }
}
```

---

### 4.3 Update Worker (Admin)
**Endpoint:** `PUT /admin/workers/{worker_id}`

**Description:** Update worker profile (admin only)

**Request Body:**
```json
{
  "name": "John Doe Updated",
  "skill": "Electrician",
  "education": "Graduate",
  "age": "31",
  "sex": "Male",
  "experience": "6",
  "location": "Delhi",
  "wage_expected": "600",
  "languages_known": "Hindi English Kannada"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Worker updated successfully"
}
```

---

### 4.4 Delete Worker (Admin)
**Endpoint:** `DELETE /admin/workers/{worker_id}`

**Description:** Delete worker profile (admin only)

**Response:**
```json
{
  "success": true,
  "message": "Worker deleted successfully"
}
```

---

### 4.5 Export Workers CSV (Admin)
**Endpoint:** `GET /admin/workers/export`

**Description:** Export all workers to CSV (admin only)

**Response:**
- Content-Type: `text/csv`
- File download with all worker data

---

## 5. Voice & Translation APIs (Optional)

### 5.1 Transcribe Audio
**Endpoint:** `POST /voice/transcribe`

**Description:** Transcribe audio to text

**Request:**
- Content-Type: `multipart/form-data`
- Field: `audio_file` (audio file)
- Field: `language`: `en-US` or `hi-IN`

**Response:**
```json
{
  "success": true,
  "transcribed_text": "Hello, how are you?",
  "language": "en-US"
}
```

---

### 5.2 Translate Text
**Endpoint:** `POST /voice/translate`

**Description:** Translate text from one language to another

**Request Body:**
```json
{
  "text": "Hello, how are you?",
  "source_language": "en",
  "target_language": "hi"
}
```

**Response:**
```json
{
  "success": true,
  "original_text": "Hello, how are you?",
  "translated_text": "नमस्ते, आप कैसे हैं?",
  "source_language": "en",
  "target_language": "hi"
}
```

---

### 5.3 Text to Speech
**Endpoint:** `POST /voice/tts`

**Description:** Convert text to speech audio

**Request Body:**
```json
{
  "text": "नमस्ते, आप कैसे हैं?",
  "language": "hi"
}
```

**Response:**
- Content-Type: `audio/mpeg`
- Audio file (MP3) in response body

---

## Error Responses

All endpoints may return these error responses:

**400 Bad Request:**
```json
{
  "success": false,
  "message": "Invalid request parameters",
  "errors": {
    "phone_number": "Phone number is required"
  }
}
```

**401 Unauthorized:**
```json
{
  "success": false,
  "message": "Unauthorized. Please login."
}
```

**404 Not Found:**
```json
{
  "success": false,
  "message": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "message": "Internal server error"
}
```

---

## Notes

1. **Phone Number Format:** 10 digits, numeric only
2. **OTP Format:** 6 digits, any number accepted (no validation in demo mode)
3. **Language Codes:** 
   - English: `en`, `en-US`
   - Hindi: `hi`, `hi-IN`
4. **Profile Created Status:**
   - `0` = Profile not created
   - `1` = Profile created (onboarding completed)
5. **Aadhaar Field:** Stored as string, no validation or normalization
6. **Authentication:** JWT tokens recommended for production

---

## Database Schema

### Workers Table
- `id` (INTEGER PRIMARY KEY)
- `timestamp` (TEXT)
- `phone_number` (TEXT)
- `profile_created` (INTEGER, 0 or 1)
- `name` (TEXT)
- `skill` (TEXT)
- `education` (TEXT)
- `age` (TEXT)
- `sex` (TEXT)
- `experience` (TEXT)
- `location` (TEXT)
- `aadhaar` (TEXT)
- `wage_expected` (TEXT)
- `languages_known` (TEXT)
- `raw_answers` (TEXT, JSON)
- `audio_path` (TEXT)

