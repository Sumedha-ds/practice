# Onboarding Voice Flow - Complete Guide

## Overview
This document explains how the voice-based onboarding works, where questions are asked via voice and user answers in voice.

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER LOGIN FIRST                         │
│  POST /api/auth/verify-otp → Get token & onboarding_status │
└─────────────────────────────────────────────────────────────┘
                            ↓
           ┌────────────────────────────────┐
           │  onboarding_completed = false? │
           └────────────────────────────────┘
                            ↓ YES
┌───────────────────────────────────────────────────────────────┐
│                    ONBOARDING PROCESS                         │
│                                                               │
│  Loop through each question (9 questions total):             │
│                                                               │
│  FOR EACH QUESTION:                                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. GET QUESTION WITH VOICE                          │    │
│  │    GET /api/onboarding/question/<question_key>      │    │
│  │    ?language=en                                     │    │
│  │                                                      │    │
│  │    Response:                                         │    │
│  │    {                                                 │    │
│  │      "question_text": "What is your name?",         │    │
│  │      "audio_base64": "base64_audio...",             │    │
│  │      "question_key": "name"                         │    │
│  │    }                                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 2. FRONTEND PLAYS AUDIO                             │    │
│  │    - Decode base64 audio                            │    │
│  │    - Play audio to user                             │    │
│  │    - User hears: "What is your name?"               │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 3. FRONTEND RECORDS USER'S VOICE ANSWER             │    │
│  │    - Start recording when user speaks               │    │
│  │    - User says: "My name is Rajesh"                 │    │
│  │    - Stop recording                                 │    │
│  │    - Create audio blob (WAV format)                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 4. SEND VOICE ANSWER TO BACKEND                     │    │
│  │    POST /api/onboarding/answer                      │    │
│  │    Content-Type: multipart/form-data                │    │
│  │                                                      │    │
│  │    Fields:                                           │    │
│  │    - audio: <audio file blob>                       │    │
│  │    - question_key: "name"                           │    │
│  │    - language: "en-US"                              │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 5. BACKEND PROCESSES VOICE                          │    │
│  │    - Receives audio file                            │    │
│  │    - Uses speech recognition                        │    │
│  │    - Converts to text: "My name is Rajesh"          │    │
│  │    - Saves answer temporarily                       │    │
│  │                                                      │    │
│  │    Response:                                         │    │
│  │    {                                                 │    │
│  │      "success": true,                               │    │
│  │      "question_key": "name",                        │    │
│  │      "answer_text": "My name is Rajesh"            │    │
│  │    }                                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ↓                                    │
│  REPEAT for all 9 questions:                                 │
│  - name                                                       │
│  - skill                                                      │
│  - education                                                  │
│  - age                                                        │
│  - sex                                                        │
│  - experience                                                 │
│  - location                                                   │
│  - wage_expected                                              │
│  - languages_known                                            │
└───────────────────────────────────────────────────────────────┘
                            ↓
┌───────────────────────────────────────────────────────────────┐
│               6. COMPLETE ONBOARDING                          │
│  POST /api/onboarding/complete                               │
│  {                                                            │
│    "answers": {                                               │
│      "name": "Rajesh",                                        │
│      "skill": "Plumber",                                      │
│      "education": "10th grade",                               │
│      ...                                                      │
│    }                                                          │
│  }                                                            │
│                                                               │
│  Backend:                                                     │
│  - Saves all answers to database                             │
│  - Sets profile_created = 1                                  │
│  - Returns success                                            │
└───────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Get Question with Voice

**Endpoint:** `GET /api/onboarding/question/<question_key>`

**Parameters:**
- `question_key`: name, skill, education, age, sex, experience, location, wage_expected, languages_known
- `language`: en (English) or hi (Hindi)

**Example:**
```bash
curl "http://localhost:5000/api/onboarding/question/name?language=en"
```

**Response:**
```json
{
  "success": true,
  "question_key": "name",
  "question_text": "What is your name?",
  "audio_base64": "//NExAAAAAANIAAAAAExBTUUzLjk4LjIAAAAAAAAA...",
  "language": "en"
}
```

### 2. Frontend Plays Audio

**JavaScript Example:**
```javascript
// Get question
const response = await fetch(`/api/onboarding/question/name?language=en`);
const data = await response.json();

// Play audio
const audio = new Audio(`data:audio/mpeg;base64,${data.audio_base64}`);
await audio.play();

// Also display text
console.log(data.question_text);
```

### 3. Frontend Records Voice Answer

**JavaScript Example:**
```javascript
// Start recording
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const mediaRecorder = new MediaRecorder(stream);
const audioChunks = [];

mediaRecorder.ondataavailable = (event) => {
  audioChunks.push(event.data);
};

mediaRecorder.start();

// User speaks...

// Stop after user finishes (or timeout)
setTimeout(() => mediaRecorder.stop(), 5000);

mediaRecorder.onstop = async () => {
  const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
  // Now send this to backend...
};
```

### 4. Send Voice Answer to Backend

**Endpoint:** `POST /api/onboarding/answer`

**Option A: With Voice (Multipart)**
```javascript
const formData = new FormData();
formData.append('audio', audioBlob, 'answer.wav');
formData.append('question_key', 'name');
formData.append('language', 'en-US');

const response = await fetch('/api/onboarding/answer', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});

const result = await response.json();
console.log('Recognized:', result.answer_text);
```

**Option B: With Text (JSON)**
```javascript
const response = await fetch('/api/onboarding/answer', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question_key: 'name',
    answer_text: 'Rajesh Kumar'
  })
});
```

### 5. Complete Onboarding

After all questions are answered, call the complete endpoint:

**Endpoint:** `POST /api/onboarding/complete`

```javascript
const response = await fetch('/api/onboarding/complete', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    answers: {
      name: 'Rajesh Kumar',
      skill: 'Plumber',
      education: '10th grade',
      age: '30',
      sex: 'Male',
      experience: '5 years',
      location: 'Mumbai',
      wage_expected: '800',
      languages_known: 'Hindi, Marathi, English'
    }
  })
});
```

## Complete Frontend Implementation

```javascript
class OnboardingVoiceFlow {
  constructor(token) {
    this.token = token;
    this.answers = {};
    this.questions = [
      'name', 'skill', 'education', 'age', 'sex', 
      'experience', 'location', 'wage_expected', 'languages_known'
    ];
    this.currentIndex = 0;
  }

  async start() {
    for (const questionKey of this.questions) {
      await this.askQuestion(questionKey);
    }
    await this.complete();
  }

  async askQuestion(questionKey) {
    // 1. Get question with voice
    const questionResponse = await fetch(
      `/api/onboarding/question/${questionKey}?language=en`,
      {
        headers: { 'Authorization': `Bearer ${this.token}` }
      }
    );
    const questionData = await questionResponse.json();

    // 2. Play audio
    const audio = new Audio(`data:audio/mpeg;base64,${questionData.audio_base64}`);
    await audio.play();

    // 3. Record user's answer
    const audioBlob = await this.recordAudio();

    // 4. Send answer to backend
    const formData = new FormData();
    formData.append('audio', audioBlob, 'answer.wav');
    formData.append('question_key', questionKey);
    formData.append('language', 'en-US');

    const answerResponse = await fetch('/api/onboarding/answer', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` },
      body: formData
    });

    const answerData = await answerResponse.json();
    this.answers[questionKey] = answerData.answer_text;
    
    console.log(`Answer for ${questionKey}:`, answerData.answer_text);
  }

  async recordAudio() {
    return new Promise((resolve) => {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
          const mediaRecorder = new MediaRecorder(stream);
          const audioChunks = [];

          mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
          };

          mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            resolve(audioBlob);
          };

          mediaRecorder.start();
          
          // Stop after 10 seconds or when user clicks stop button
          setTimeout(() => mediaRecorder.stop(), 10000);
        });
    });
  }

  async complete() {
    const response = await fetch('/api/onboarding/complete', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ answers: this.answers })
    });

    const result = await response.json();
    console.log('Onboarding complete:', result);
  }
}

// Usage
const token = 'token_9876543210_1234';
const onboarding = new OnboardingVoiceFlow(token);
await onboarding.start();
```

## API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/onboarding/questions` | Get all questions (text only) |
| GET | `/api/onboarding/question/<key>` | Get single question with voice audio |
| POST | `/api/onboarding/answer` | Save single answer (voice or text) |
| POST | `/api/onboarding/complete` | Complete onboarding with all answers |

## Audio Format Requirements

- **For sending voice answers:** WAV, FLAC, or AIFF (MP3 not supported)
- **For question audio:** MP3 (base64 encoded)

## Error Handling

```javascript
try {
  const response = await fetch('/api/onboarding/answer', {...});
  const data = await response.json();
  
  if (!data.success) {
    if (data.message.includes('Could not understand')) {
      // Ask user to repeat
      alert('Could not understand. Please speak again.');
    } else if (data.message.includes('Unsupported audio format')) {
      // Audio format issue
      alert('Please use WAV format for recording.');
    }
  }
} catch (error) {
  console.error('Error:', error);
}
```

## Testing

See `TEST_VOICE_RECOGNITION.md` for testing instructions.

## Notes

1. **Sequential Processing:** Questions are asked one by one, waiting for each answer before moving to next
2. **Temporary Storage:** Answers are saved temporarily as they're collected
3. **Final Save:** `complete_onboarding` endpoint finalizes all answers and sets `profile_created = 1`
4. **Language Support:** Both English (`en`) and Hindi (`hi`) supported for questions
5. **Speech Recognition:** Uses Google Speech Recognition for converting voice to text

