# Testing Voice Choice Recognition

## Quick Test Steps

### 1. Start the Server
```bash
cd /Users/dealshare/Main
source venv/bin/activate
python api_server.py
```

### 2. Test with Text Input (Easiest)
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "9876543210", "otp": "123456"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

# Test with text
curl -X POST http://localhost:5000/api/auth/user-choice \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"voice_text": "I want to apply for job"}'
```

### 3. Test with Audio File Upload (Multipart)

**Using curl:**
```bash
# Get token first
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "9876543210", "otp": "123456"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

# Upload audio file (WAV format recommended)
curl -X POST http://localhost:5000/api/auth/user-choice/recognize \
  -H "Authorization: Bearer $TOKEN" \
  -F "audio=@/path/to/recording.wav" \
  -F "language=en-US"
```

**Using Python:**
```python
import requests

# Get token
response = requests.post('http://localhost:5000/api/auth/verify-otp',
    json={'phone_number': '9876543210', 'otp': '123456'})
token = response.json()['token']

# Upload audio file
with open('recording.wav', 'rb') as audio_file:
    files = {'audio': ('recording.wav', audio_file, 'audio/wav')}
    data = {'language': 'en-US'}
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(
        'http://localhost:5000/api/auth/user-choice/recognize',
        headers=headers,
        files=files,
        data=data
    )
    
    print(response.json())
```

**Using Postman:**
1. Method: `POST`
2. URL: `http://localhost:5000/api/auth/user-choice/recognize`
3. Headers:
   - `Authorization: Bearer <token>`
4. Body: Select `form-data`
   - Key: `audio` (type: File)
   - Value: Select your WAV audio file
   - Key: `language` (type: Text)
   - Value: `en-US`

## Expected Responses

### Success Response:
```json
{
  "success": true,
  "user_choice": "apply_job",
  "recognized_text": "I want to apply for job",
  "phone_number": "9876543210"
}
```

### Error Response (if audio not understood):
```json
{
  "success": false,
  "message": "Could not understand audio. Please try again."
}
```

## Supported Audio Formats
- **WAV** (recommended - most reliable)
- **FLAC**
- **AIFF**

**Note:** MP3 files may not work directly with `speech_recognition` library. Convert to WAV if needed.

## Testing with Real Voice Recording

1. Record audio saying: "apply job", "post job", or "learning module"
2. Save as WAV format
3. Upload using one of the methods above
4. Check the `user_choice` in the response

## Troubleshooting

- **"Audio file is required"**: Make sure you're sending the file with field name `audio`
- **"Could not understand audio"**: The speech recognition couldn't process the audio. Try:
  - Use WAV format
  - Ensure audio is clear
  - Check language parameter matches the spoken language
- **"Unauthorized"**: Make sure you have a valid token from `/api/auth/verify-otp`

