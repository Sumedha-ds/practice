# Hindi Language Support

## Configuration

The system is now configured for **Hindi audio by default**.

## Speech Recognition

- **Default Language:** `hi-IN` (Hindi - India)
- The system will recognize Hindi speech automatically
- No need to pass language parameter from frontend

## Supported Keywords

### Apply Job (नौकरी लागू करें)
**Hindi:**
- अप्लाई (apply)
- जॉब (job)
- नौकरी (job/work)
- काम (work)

**English (also works):**
- apply, job, apply job, find job, search job

### Post Job (नौकरी पोस्ट करें)
**Hindi:**
- पोस्ट (post)
- नौकरी देना (give job)

**English (also works):**
- post, post job, create job, add job

### Learning Module (सीखने का मॉड्यूल)
**Hindi:**
- सीखना (learn)
- शिक्षा (education)
- पढ़ाई (study)

**English (also works):**
- learn, learning, education, course

## Frontend Usage

### Don't need to specify language anymore:

```javascript
// Before (optional)
formData.append('language', 'hi-IN');

// Now (defaults to Hindi automatically)
const formData = new FormData();
formData.append('audio', hindiAudioBlob, 'recording.wav');
// language parameter is optional, defaults to hi-IN
```

### Full Example:

```javascript
const formData = new FormData();
formData.append('audio', hindiAudioBlob, 'recording.wav');

fetch('http://172.24.45.88:5000/api/auth/user-choice/recognize', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

## Example Responses

### User says: "अप्लाई जॉब"
```json
{
  "success": true,
  "user_choice": "apply_job",
  "recognized_text": "अप्लाई जॉब",
  "phone_number": "9876543210"
}
```

### User says: "पोस्ट जॉब"
```json
{
  "success": true,
  "user_choice": "post_job",
  "recognized_text": "पोस्ट जॉब",
  "phone_number": "9876543210"
}
```

### User says: "सीखना"
```json
{
  "success": true,
  "user_choice": "learning_module",
  "recognized_text": "सीखना",
  "phone_number": "9876543210"
}
```

## Onboarding Questions

All onboarding questions also support Hindi:

```javascript
// Get question in Hindi
GET /api/onboarding/question/name?language=hi

// Response will have Hindi question and audio
{
  "question_text": "आपका नाम क्या है?",
  "audio_base64": "...",
  "language": "hi"
}
```

## Notes

✅ System defaults to Hindi (hi-IN)
✅ Recognizes both Hindi and English keywords
✅ No language parameter needed from frontend
✅ Works with Devanagari script (Hindi text)
✅ Question audio can be in Hindi or English

## Testing

Test with Hindi audio:
- "अप्लाई जॉब" → apply_job ✅
- "पोस्ट जॉब" → post_job ✅
- "सीखना चाहता हूं" → learning_module ✅

