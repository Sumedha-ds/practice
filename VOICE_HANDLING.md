# Voice Handling - How Frontend Sends Voice to Backend

## Overview
When the frontend collects voice from the user, it needs to send that voice data to the backend for processing. The backend handles speech recognition and determines the user's choice.

## How It Works

### Flow:
```
1. Frontend plays question audio (from GET /api/auth/user-choice/question)
   ↓
2. Frontend records user's voice response
   ↓
3. Frontend sends voice audio to backend
   ↓
4. Backend performs speech recognition
   ↓
5. Backend processes recognized text to determine choice
   ↓
6. Backend saves choice and returns response
```

## API Endpoint: POST /api/auth/user-choice/recognize

This endpoint accepts voice audio as **multipart file upload**.

**Content-Type:** `multipart/form-data`

**Request Fields:**
- `audio` (required): Audio file (WAV, FLAC, or AIFF)
- `language` (optional): Language code (default: `en-US`)

**Frontend Example (JavaScript):**
```javascript
// Record audio using MediaRecorder API
const mediaRecorder = new MediaRecorder(stream);
const audioChunks = [];

mediaRecorder.ondataavailable = (event) => {
  audioChunks.push(event.data);
};

mediaRecorder.onstop = async () => {
  // Create audio blob (WAV format recommended)
  const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
  
  // Create FormData
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.wav');
  formData.append('language', 'en-US');
  
  // Send to backend
  const response = await fetch('/api/auth/user-choice/recognize', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
      // Don't set Content-Type header - browser will set it with boundary
    },
    body: formData
  });
  
  const result = await response.json();
  console.log('User choice:', result.user_choice);
};
```

---

## Response Format

**Success Response:**
```json
{
  "success": true,
  "user_choice": "apply_job",
  "recognized_text": "I want to apply for job",
  "phone_number": "9876543210"
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Could not understand your choice. Please say: apply job, post job, or learning module.",
  "recognized_text": "some unclear text"
}
```

## Supported Audio Formats

- **WAV** (recommended)
- **FLAC**
- **AIFF**

**Note:** The audio should be in a format supported by `speech_recognition` library. WAV format is most reliable.

## Language Support

The `language` parameter supports:
- `en-US` - English (US)
- `hi-IN` - Hindi (India)
- Other Google Speech Recognition language codes

## Complete Frontend Example

```javascript
// Step 1: Get question and play it
async function askUserChoice(token) {
  const questionResponse = await fetch('/api/auth/user-choice/question?language=en', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const question = await questionResponse.json();
  
  // Play audio
  const audio = new Audio('data:audio/mpeg;base64,' + question.audio_base64);
  await audio.play();
  
  // Step 2: Record user's voice response
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mediaRecorder = new MediaRecorder(stream);
  const audioChunks = [];
  
  mediaRecorder.ondataavailable = (event) => {
    audioChunks.push(event.data);
  };
  
  return new Promise((resolve) => {
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
      
      // Step 3: Send voice to backend
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');
      formData.append('language', 'en-US');
      
      const response = await fetch('/api/auth/user-choice/recognize', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      const result = await response.json();
      resolve(result);
    };
    
    mediaRecorder.start();
    // Stop after 5 seconds or when user stops
    setTimeout(() => mediaRecorder.stop(), 5000);
  });
}
```

## Backend Processing

1. **Receives audio** in one of the supported formats
2. **Converts to audio data** that speech_recognition can process
3. **Calls Google Speech Recognition API** to convert speech to text
4. **Processes text** to determine user choice:
   - Keywords for "apply job": apply, job, apply job, find job, search job
   - Keywords for "post job": post, post job, create job, add job
   - Keywords for "learning module": learn, learning, learning module, education, course
5. **Saves choice** to database
6. **Returns response** with user_choice

## Error Handling

The backend handles:
- Invalid audio formats
- Unrecognized speech
- Network errors
- Missing audio data

All errors return appropriate error messages to help frontend handle them gracefully.

