# Complete Onboarding Flow with curl Examples

## Overview
User answers onboarding questions one by one. **Each answer is saved immediately** after user speaks.

## Flow Diagram

```
┌────────────────────────────────────────────────────────────┐
│                    1. USER LOGIN                           │
│  POST /api/auth/verify-otp                                 │
│  Get token + check if onboarding completed                │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│           2. FOR EACH QUESTION (9 questions)               │
│                                                            │
│  Step A: GET QUESTION WITH AUDIO                          │
│  GET /api/onboarding/question/<question_key>              │
│  → Returns Hindi question text + audio (base64)           │
│                                                            │
│  Step B: PLAY AUDIO TO USER                               │
│  → Frontend plays the audio                               │
│  → User hears question in Hindi                           │
│                                                            │
│  Step C: RECORD USER'S VOICE ANSWER                       │
│  → Frontend records user speaking (WAV format)            │
│  → User answers in Hindi                                  │
│                                                            │
│  Step D: SEND VOICE TO BACKEND IMMEDIATELY                │
│  POST /api/onboarding/answer                              │
│  → Backend converts speech to text                        │
│  → Backend saves answer to database                       │
│  → Returns recognized text                                │
│                                                            │
│  ✅ Answer saved! Move to next question                   │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│         3. COMPLETE ONBOARDING (Optional)                  │
│  POST /api/onboarding/complete                            │
│  → Sets profile_created = 1                               │
│  → User is now fully onboarded                            │
└────────────────────────────────────────────────────────────┘
```

## Complete curl Examples

### Step 1: Login and Get Token

```bash
# Login with phone number and OTP
curl -X POST http://172.24.45.88:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "9876543210",
    "otp": "1234"
  }'
```

**Response:**
```json
{
  "phone_number": "9876543210",
  "onboarding_completed": false,
  "token": "token_9876543210_1234"
}
```

**Save the token** - you'll need it for all subsequent requests.

---

### Step 2: Onboarding Questions (Loop through 9 questions)

#### Question Keys (in order):
1. `name` - What is your name?
2. `skill` - What is your skill?
3. `education` - What is your education level?
4. `age` - What is your age?
5. `sex` - What is your sex?
6. `experience` - How many years of experience?
7. `location` - Which city are you from?
8. `wage_expected` - What is your expected daily wage?
9. `languages_known` - Which languages do you know?

---

#### Example: Question 1 - Name

**2A. Get Question with Audio:**
```bash
curl -X GET "http://172.24.45.88:5000/api/onboarding/question/name?language=hi"
```

**Response:**
```json
{
  "success": true,
  "question_key": "name",
  "question_text": "आपका नाम क्या है?",
  "audio_base64": "//NExAAAAAANIAAAAAExBTUUzLjk4LjI...",
  "language": "hi"
}
```

**2B. Frontend Action:**
- Decode base64 audio
- Play audio to user
- User hears: "आपका नाम क्या है?" (What is your name?)

**2C. Frontend Action:**
- Start recording when user speaks
- User says: "मेरा नाम राजेश कुमार है"
- Stop recording
- Create WAV blob

**2D. Send Voice Answer Immediately:**
```bash
# Note: This is for curl testing. Frontend will send FormData with actual audio file.
curl -X POST http://172.24.45.88:5000/api/onboarding/answer \
  -H "Authorization: Bearer token_9876543210_1234" \
  -F "audio=@answer_name.wav" \
  -F "question_key=name" \
  -F "language=hi-IN"
```

**Response:**
```json
{
  "success": true,
  "question_key": "name",
  "answer_text": "राजेश कुमार",
  "phone_number": "9876543210"
}
```

✅ **Answer saved immediately in database!**

---

#### Example: Question 2 - Skill

**Get Question:**
```bash
curl -X GET "http://172.24.45.88:5000/api/onboarding/question/skill?language=hi"
```

**Response:**
```json
{
  "success": true,
  "question_key": "skill",
  "question_text": "आपका कौशल क्या है? जैसे: पलंबर, पेंटर, इलेक्ट्रीशियन?",
  "audio_base64": "...",
  "language": "hi"
}
```

**Send Answer:**
```bash
curl -X POST http://172.24.45.88:5000/api/onboarding/answer \
  -H "Authorization: Bearer token_9876543210_1234" \
  -F "audio=@answer_skill.wav" \
  -F "question_key=skill"
```

**Response:**
```json
{
  "success": true,
  "question_key": "skill",
  "answer_text": "प्लंबर",
  "phone_number": "9876543210"
}
```

✅ **Answer saved!**

---

### Continue for All 9 Questions

Repeat the same process for:
- `education`
- `age`
- `sex`
- `experience`
- `location`
- `wage_expected`
- `languages_known`

---

### Step 3: Complete Onboarding

After all questions are answered, call the complete endpoint:

```bash
curl -X POST http://172.24.45.88:5000/api/onboarding/complete \
  -H "Authorization: Bearer token_9876543210_1234" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": {
      "name": "राजेश कुमार",
      "skill": "प्लंबर",
      "education": "10वीं कक्षा",
      "age": "30",
      "sex": "पुरुष",
      "experience": "5 साल",
      "location": "मुंबई",
      "wage_expected": "800",
      "languages_known": "हिंदी, मराठी"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Onboarding complete and saved",
  "phone_number": "9876543210",
  "profile_created": true
}
```

---

## Frontend Implementation (JavaScript)

```javascript
// Configuration
const BASE_URL = 'http://172.24.45.88:5000';
const questions = [
  'name', 'skill', 'education', 'age', 'sex',
  'experience', 'location', 'wage_expected', 'languages_known'
];

// 1. Login
async function login(phoneNumber, otp) {
  const response = await fetch(`${BASE_URL}/api/auth/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      phone_number: phoneNumber,
      otp: otp 
    })
  });
  
  const data = await response.json();
  return data.token;
}

// 2. Complete Onboarding Flow
async function completeOnboarding(token) {
  const allAnswers = {};
  
  for (const questionKey of questions) {
    // A. Get question with audio
    const questionResponse = await fetch(
      `${BASE_URL}/api/onboarding/question/${questionKey}?language=hi`
    );
    const question = await questionResponse.json();
    
    // B. Play audio to user
    const audio = new Audio(`data:audio/mpeg;base64,${question.audio_base64}`);
    await audio.play();
    await waitForAudioEnd(audio);
    
    // C. Record user's voice
    console.log(`Recording answer for: ${question.question_text}`);
    const audioBlob = await recordUserVoice();
    
    // D. Send answer immediately
    const formData = new FormData();
    formData.append('audio', audioBlob, 'answer.wav');
    formData.append('question_key', questionKey);
    
    const answerResponse = await fetch(
      `${BASE_URL}/api/onboarding/answer`,
      {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      }
    );
    
    const answerData = await answerResponse.json();
    console.log(`✅ Saved: ${answerData.answer_text}`);
    
    // Store answer
    allAnswers[questionKey] = answerData.answer_text;
  }
  
  // 3. Complete onboarding (marks profile as complete)
  await fetch(`${BASE_URL}/api/onboarding/complete`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ answers: allAnswers })
  });
  
  console.log('✅ Onboarding completed!');
}

// Helper: Record audio from microphone
async function recordUserVoice() {
  return new Promise(async (resolve) => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    const audioChunks = [];
    
    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data);
    };
    
    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
      stream.getTracks().forEach(track => track.stop());
      resolve(audioBlob);
    };
    
    mediaRecorder.start();
    
    // Stop after 10 seconds or when user clicks stop button
    setTimeout(() => mediaRecorder.stop(), 10000);
  });
}

// Helper: Wait for audio to finish playing
function waitForAudioEnd(audio) {
  return new Promise(resolve => {
    audio.onended = resolve;
  });
}

// Usage
const token = await login('9876543210', '1234');
await completeOnboarding(token);
```

---

## Key Points for Frontend Engineer

### 1. **Immediate Save**
- ✅ Each answer is saved immediately after recording
- ✅ No need to wait for all 9 questions
- ✅ If user closes app, already answered questions are saved

### 2. **Audio Format**
- ✅ Must be WAV format (not MP3)
- ✅ Send as multipart/form-data
- ✅ Language defaults to Hindi (hi-IN)

### 3. **Error Handling**
```javascript
const answerResponse = await fetch(...);
const result = await answerResponse.json();

if (!result.success) {
  if (result.message.includes('Could not understand')) {
    // Ask user to repeat
    alert('कृपया फिर से बोलें (Please speak again)');
    // Re-record for same question
  }
}
```

### 4. **Progress Tracking**
```javascript
// Show progress to user
console.log(`Question ${index + 1} of ${questions.length}`);
// Update progress bar: (index + 1) / questions.length * 100
```

### 5. **Resume Capability**
Since answers are saved immediately, user can resume later:
```javascript
// Check which questions are already answered
const profile = await fetch(`${BASE_URL}/api/worker/profile`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
// Start from first unanswered question
```

---

## API Summary

| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/api/auth/verify-otp` | POST | Login | No |
| `/api/onboarding/question/<key>` | GET | Get question + audio | No |
| `/api/onboarding/answer` | POST | Save single answer | Yes |
| `/api/onboarding/complete` | POST | Mark onboarding done | Yes |

---

## Testing the Complete Flow

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://172.24.45.88:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"9999999999","otp":"1234"}' | \
  grep -o '"token":"[^"]*' | cut -d'"' -f4)

echo "Token: $TOKEN"

# 2. Get first question
curl -s "http://172.24.45.88:5000/api/onboarding/question/name?language=hi" | \
  python3 -m json.tool

# 3. Send answer (with real audio file)
curl -X POST http://172.24.45.88:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -F "audio=@test_audio.wav" \
  -F "question_key=name"

# Repeat for all questions...

# 4. Complete onboarding
curl -X POST http://172.24.45.88:5000/api/onboarding/complete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": {
      "name": "Test User",
      "skill": "Plumber",
      "education": "10th",
      "age": "30",
      "sex": "Male",
      "experience": "5",
      "location": "Mumbai",
      "wage_expected": "800",
      "languages_known": "Hindi"
    }
  }'
```

---

## Server URLs

**Development (local):**
- `http://localhost:5000`

**Network (from other devices):**
- `http://172.24.45.88:5000`

Both servers must be on same Wi-Fi network.

