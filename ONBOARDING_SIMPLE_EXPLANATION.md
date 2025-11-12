# Onboarding with Voice - Simple Explanation

## The Problem
Frontend needs to:
1. Ask questions in voice
2. Get user's voice answers
3. Save all answers

## The Solution - How It Works

### Step-by-Step Process

```
┌──────────────────────────────────────────────────────────────┐
│  FRONTEND                          BACKEND                   │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Question 1: "What is your name?"                            │
│  ───────────────────────────────────────────────────────     │
│                                                               │
│  1. Request question with audio                              │
│     GET /api/onboarding/question/name?language=en            │
│     ────────────────────────────────────────────>            │
│                                                               │
│                                    2. Generate TTS audio     │
│                                       Convert text to MP3    │
│                                       Encode as base64       │
│                                                               │
│     3. Receive question + audio                              │
│     <────────────────────────────────────────────            │
│     {                                                         │
│       "question_text": "What is your name?",                 │
│       "audio_base64": "//NExAAA..."                          │
│     }                                                         │
│                                                               │
│  4. Play audio to user                                       │
│     🔊 "What is your name?"                                  │
│                                                               │
│  5. Record user's voice                                      │
│     🎤 User says: "My name is Rajesh"                        │
│     Save as WAV file (audioBlob)                             │
│                                                               │
│  6. Send voice to backend                                    │
│     POST /api/onboarding/answer                              │
│     FormData:                                                 │
│       - audio: audioBlob (WAV file)                          │
│       - question_key: "name"                                 │
│       - language: "en-US"                                    │
│     ────────────────────────────────────────────>            │
│                                                               │
│                                    7. Process voice           │
│                                       - Read WAV file         │
│                                       - Use Google Speech API│
│                                       - Convert to text       │
│                                       - Save: "Rajesh"        │
│                                                               │
│     8. Receive confirmation                                  │
│     <────────────────────────────────────────────            │
│     {                                                         │
│       "success": true,                                       │
│       "answer_text": "Rajesh"                               │
│     }                                                         │
│                                                               │
│  ─────────────────────────────────────────────────────────  │
│  REPEAT FOR ALL 9 QUESTIONS                                  │
│  ─────────────────────────────────────────────────────────  │
│                                                               │
│  9. Complete onboarding                                      │
│     POST /api/onboarding/complete                            │
│     {                                                         │
│       "answers": {                                            │
│         "name": "Rajesh",                                    │
│         "skill": "Plumber",                                  │
│         ... all 9 answers                                    │
│       }                                                       │
│     }                                                         │
│     ────────────────────────────────────────────>            │
│                                                               │
│                                    10. Save to database       │
│                                        Set profile_created=1 │
│                                                               │
│     11. Done!                                                │
│     <────────────────────────────────────────────            │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Three Key APIs

### 1. Get Question with Voice
```
GET /api/onboarding/question/{question_key}?language=en

Response:
{
  "question_text": "What is your name?",
  "audio_base64": "base64_encoded_mp3_audio",
  "question_key": "name"
}
```

### 2. Save Answer (Voice or Text)
```
POST /api/onboarding/answer
Headers: Authorization: Bearer <token>

Option A - Voice (multipart/form-data):
  - audio: <WAV file>
  - question_key: "name"
  - language: "en-US"

Option B - Text (application/json):
  {
    "question_key": "name",
    "answer_text": "Rajesh"
  }

Response:
{
  "success": true,
  "answer_text": "Rajesh",
  "question_key": "name"
}
```

### 3. Complete Onboarding
```
POST /api/onboarding/complete
Headers: Authorization: Bearer <token>

Body:
{
  "answers": {
    "name": "Rajesh Kumar",
    "skill": "Plumber",
    "education": "10th grade",
    "age": "30",
    "sex": "Male",
    "experience": "5 years",
    "location": "Mumbai",
    "wage_expected": "800",
    "languages_known": "Hindi, English"
  }
}
```

## The 9 Questions

1. **name** - What is your name?
2. **skill** - What is your skill?
3. **education** - What is your education level?
4. **age** - What is your age?
5. **sex** - What is your sex?
6. **experience** - How many years of experience?
7. **location** - Which city or village are you from?
8. **wage_expected** - What is your expected daily wage?
9. **languages_known** - Which languages do you know?

## Simple Frontend Code

```javascript
// List of all questions
const questions = [
  'name', 'skill', 'education', 'age', 'sex',
  'experience', 'location', 'wage_expected', 'languages_known'
];

const answers = {};

// Loop through each question
for (const questionKey of questions) {
  // 1. Get question with audio
  const response = await fetch(
    `/api/onboarding/question/${questionKey}?language=en`
  );
  const data = await response.json();
  
  // 2. Play audio
  const audio = new Audio(`data:audio/mpeg;base64,${data.audio_base64}`);
  await audio.play();
  
  // 3. Record user's voice
  const audioBlob = await recordUserVoice(); // Your recording function
  
  // 4. Send voice to backend
  const formData = new FormData();
  formData.append('audio', audioBlob, 'answer.wav');
  formData.append('question_key', questionKey);
  formData.append('language', 'en-US');
  
  const answerResponse = await fetch('/api/onboarding/answer', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  const answerData = await answerResponse.json();
  answers[questionKey] = answerData.answer_text;
  
  console.log(`Saved ${questionKey}: ${answerData.answer_text}`);
}

// 5. Complete onboarding
await fetch('/api/onboarding/complete', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ answers })
});

console.log('Onboarding complete!');
```

## What Backend Does

### When Frontend Requests Question:
1. Gets question text in specified language (en/hi)
2. Converts text to speech using Google TTS
3. Encodes audio as base64
4. Sends back JSON with text + audio

### When Frontend Sends Voice Answer:
1. Receives WAV audio file
2. Uses Google Speech Recognition to convert to text
3. Saves answer temporarily in database
4. Returns recognized text to frontend

### When Frontend Completes Onboarding:
1. Gets all saved answers
2. Updates user profile in database
3. Sets `profile_created = 1`
4. User is now fully onboarded

## Audio Formats

| Direction | Format | Why |
|-----------|--------|-----|
| Backend → Frontend (questions) | MP3 (base64) | Small size, plays in browser |
| Frontend → Backend (answers) | WAV | Required by speech recognition |

## Important Notes

1. **Sequential Process**: Ask one question at a time, wait for answer
2. **Temporary Storage**: Answers saved as they're collected
3. **Final Save**: `complete_onboarding` finalizes everything
4. **Error Handling**: If voice not understood, user can repeat
5. **Language Support**: Both English and Hindi supported

## Testing

The endpoints are working! Test results:
- ✅ Get question with voice: Working
- ✅ Save voice answer: Working  
- ✅ Complete onboarding: Working

See `ONBOARDING_VOICE_FLOW.md` for detailed implementation.

