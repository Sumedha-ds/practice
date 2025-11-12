# User Choice Flow - After Login

## Overview
As soon as user logs in (after OTP verification), the system asks them via voice what they want to do.

## Complete Flow

```
1. User enters phone number and OTP
   ↓
2. POST /api/auth/verify-otp
   ↓
3. Get response with token and onboarding_completed status
   ↓
4. IMMEDIATELY after login (regardless of onboarding status):
   → GET /api/auth/user-choice/question (get voice question)
   → Play audio question: "What would you like to do? Say apply job, post job, or learning module."
   → Collect voice response from user
   ↓
5. Process voice response:
   Option A: Frontend does speech recognition
   → POST /api/auth/user-choice (with voice_text)
   
   Option B: Send audio file directly
   → POST /api/auth/user-choice/recognize (with audio file)
   ↓
6. Get user_choice in response:
   - "apply_job"
   - "post_job"  
   - "learning_module"
   ↓
7. Redirect user based on choice:
   - apply_job → Job search/application page
   - post_job → Job posting page
   - learning_module → Learning/training page
   ↓
8. If onboarding_completed = false:
   → Also start onboarding flow (can happen in parallel or after choice)
```

## API Flow

### Step 1: Verify OTP
```
POST /api/auth/verify-otp
Body: {
  "phone_number": "1234567890",
  "otp": "123456"
}
Response: {
  "phone_number": "1234567890",
  "onboarding_completed": true/false,
  "token": "token_1234567890_1234"
}
```

### Step 2: Get User Choice Question (Immediately after login)
```
GET /api/auth/user-choice/question?language=en
Headers: {
  "Authorization": "Bearer <token>"
}
Response: {
  "success": true,
  "question_text": "What would you like to do? Say apply job, post job, or learning module.",
  "audio_base64": "base64_encoded_audio",
  "language": "en"
}
```

### Step 3: Play Audio & Collect Voice Response
Frontend plays the audio_base64, then collects user's voice response.

### Step 4: Submit Voice Response
**Option A: With recognized text**
```
POST /api/auth/user-choice
Headers: {
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
Body: {
  "voice_text": "I want to apply for job"
}
Response: {
  "success": true,
  "user_choice": "apply_job",
  "phone_number": "1234567890",
  "recognized_text": "I want to apply for job"
}
```

**Option B: With audio file**
```
POST /api/auth/user-choice/recognize
Headers: {
  "Authorization": "Bearer <token>"
}
Body (multipart/form-data): {
  "audio": <audio_file>,
  "language": "en-US"
}
Response: {
  "success": true,
  "user_choice": "apply_job",
  "recognized_text": "I want to apply for job",
  "phone_number": "1234567890"
}
```

## Important Points

1. **Timing**: User choice question is asked IMMEDIATELY after login, regardless of onboarding status
2. **Voice-based**: Question is asked via voice (TTS), response collected via voice (STT)
3. **Three Options**: 
   - `apply_job` - User wants to apply for jobs
   - `post_job` - User wants to post a job
   - `learning_module` - User wants to access learning module
4. **Choice is Saved**: User's choice is saved in database and returned in future verify-otp calls
5. **Onboarding**: If onboarding is not completed, it can happen after or alongside user choice selection

## Frontend Implementation Example

```javascript
// After verify OTP
const loginResponse = await verifyOTP(phone, otp);
const token = loginResponse.token;

// Immediately ask user choice
const questionResponse = await getUserChoiceQuestion(token);
const audioBase64 = questionResponse.audio_base64;

// Play audio
playAudio(audioBase64);

// Collect voice response
const voiceText = await recognizeVoice(); // Frontend speech recognition

// Submit choice
const choiceResponse = await saveUserChoice(token, voiceText);
const userChoice = choiceResponse.user_choice;

// Redirect based on choice
if (userChoice === 'apply_job') {
  redirectTo('/jobs/apply');
} else if (userChoice === 'post_job') {
  redirectTo('/jobs/post');
} else if (userChoice === 'learning_module') {
  redirectTo('/learning');
}
```

