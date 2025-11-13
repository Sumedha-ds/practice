# 🎯 HACKATHON DEMO WORKFLOW

## Voice-Based Onboarding System with Smart Validations

---

## 🚀 Quick Start

### 1. Start the Server
```bash
cd /Users/dealshare/Main
source venv/bin/activate
python api_server.py
```

Server will start on:
- **Local:** http://localhost:5000
- **Network:** http://YOUR_IP:5000

---

## 📱 Demo Script (5 Minutes)

### **Part 1: Basic Flow (2 min)**

#### Step 1: User Login
```bash
curl -X POST http://localhost:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"9988776655","otp":"1234"}'
```

**Response:**
```json
{
  "success": true,
  "phone_number": "9988776655",
  "onboarding_completed": false,
  "token": "token_9988776655_xxxx"
}
```

**Explain:**
- Simple OTP-based login
- Any 4-digit OTP accepted
- Token generated for session
- Checks if onboarding is completed

---

#### Step 2: User Choice (Apply Job / Post Job / Learning)
```bash
# For demonstration with audio file
curl -X POST http://localhost:5000/api/auth/user-choice/recognize \
  -H "Authorization: Bearer $TOKEN" \
  -F "audio=@hindi_audio.wav"
```

**Explain:**
- User speaks their choice in Hindi
- System recognizes: "apply job" / "post job" / "learning module"
- Extensive Hindi keyword matching

---

### **Part 2: Smart Validations (3 min)**

#### Scenario 1: Invalid Name
```bash
curl -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"name","answer_text":"123 invalid"}'
```

**Response:**
```json
{
  "success": false,
  "valid": false,
  "error_message": "कृपया केवल अपना नाम बताएं।",
  "error_audio": "base64_encoded_hindi_voice",
  "question_key": "name",
  "received_text": "123 invalid"
}
```

**Explain:**
- ❌ Validation failed (contains numbers)
- Error message in **Hindi** (user's language)
- Voice feedback available as base64 MP3
- User can hear the error message

---

#### Scenario 2: Valid Name
```bash
curl -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"name","answer_text":"My name is Rajesh Kumar"}'
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "question_key": "name",
  "answer_text": "Rajesh Kumar",
  "original_text": "my name is rajesh kumar",
  "phone_number": "9988776655"
}
```

**Explain:**
- ✅ Validation passed
- Filler words removed ("my", "name", "is")
- Name cleaned and capitalized
- Ready to save to database

---

#### Scenario 3: Invalid Age
```bash
curl -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"age","answer_text":"I am 150 years old"}'
```

**Response:**
```json
{
  "success": false,
  "valid": false,
  "error_message": "कृपया 16 से 70 के बीच अपनी सही उम्र बताएं।",
  "error_audio": "base64_encoded_hindi_voice",
  "question_key": "age",
  "received_text": "I am 150 years old"
}
```

**Explain:**
- ❌ Age out of range (16-70)
- Hindi error message
- Voice feedback available

---

#### Scenario 4: Valid Age
```bash
curl -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"age","answer_text":"I am 28 years old"}'
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "question_key": "age",
  "answer_text": "28",
  "original_text": "I am 28 years old",
  "phone_number": "9988776655"
}
```

**Explain:**
- ✅ Number extracted and validated
- Clean numeric value saved

---

#### Scenario 5: Job Validation (Fuzzy Match)
```bash
curl -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"skill","answer_text":"I am a paintr"}'  # Typo!
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "question_key": "skill",
  "answer_text": "painter",
  "original_text": "I am a paintr",
  "phone_number": "9988776655"
}
```

**Explain:**
- ✅ Fuzzy matching corrected the typo
- "paintr" → "painter"
- Matches against 80+ job categories

---

#### Scenario 6: Fresher Recognition
```bash
curl -X POST http://localhost:5000/api/onboarding/answer \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_key":"experience","answer_text":"I am a fresher"}'
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "question_key": "experience",
  "answer_text": "Fresher",
  "original_text": "I am a fresher",
  "phone_number": "9988776655"
}
```

**Explain:**
- ✅ Recognized "fresher" keyword
- No experience required

---

## 🎬 Live Demo Tips

### Setup Before Demo:
1. Start both servers (Flask + FastAPI)
2. Have Postman ready with sample requests
3. Have a few audio files for voice demo
4. Clear database for fresh demo

### During Demo:
1. **Show the problem:** Illiterate job seekers need voice interface
2. **Show the solution:** Voice-based onboarding with validations
3. **Highlight key features:**
   - Hindi language support
   - Smart validations
   - Voice error feedback
   - Fuzzy matching
   - Real-time processing

### Key Talking Points:
- ✅ **80+ job categories** recognized
- ✅ **Fuzzy matching** handles typos
- ✅ **Hindi support** for error messages
- ✅ **Voice feedback** for illiterate users
- ✅ **Real-time validation** saves time
- ✅ **Data cleaning** ensures quality

---

## 🧪 Run Full Test Suite

```bash
cd /Users/dealshare/Main
source venv/bin/activate
python test_validations.py
```

This will test:
- ✅ Name validation (valid/invalid)
- ✅ Age validation (valid/invalid)
- ✅ Skill validation with fuzzy matching
- ✅ Experience validation with "fresher"
- ✅ Location validation
- ✅ Gender validation

---

## 📊 Expected Output

```
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯
SMART VALIDATION DEMO - Voice Onboarding System
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯

============================================================
  STEP 1: Login
============================================================

Status: 200
{
  "success": true,
  "token": "token_9988776655_xxxx"
}

✅ Login successful!

============================================================
  Testing: NAME
============================================================

📝 Test 1: Answering with '123 invalid'
❌ INVALID
   Error: कृपया केवल अपना नाम बताएं।

📝 Test 2: Answering with 'Rajesh Kumar'
✅ VALID - Saved as: 'Rajesh Kumar'

============================================================
  Testing: AGE
============================================================

📝 Test 1: Answering with '150'
❌ INVALID
   Error: कृपया 16 से 70 के बीच अपनी सही उम्र बताएं।

📝 Test 2: Answering with '28'
✅ VALID - Saved as: '28'

✅ VALIDATION DEMO COMPLETE!
```

---

## 🏆 Judging Criteria Alignment

| Criteria | How We Address It |
|----------|-------------------|
| **Innovation** | Voice-first interface for illiterate users + Smart validations |
| **Technical Complexity** | Speech recognition + Translation + NLP validation + Fuzzy matching |
| **User Experience** | Hindi support + Voice feedback + Real-time validation |
| **Scalability** | Modular design + Database-backed + REST API |
| **Social Impact** | Empowering illiterate job seekers in India |

---

## 📞 Q&A Preparation

**Q: What if the user speaks in a regional language?**
A: Currently supports Hindi, but the architecture is extensible for Tamil, Telugu, etc.

**Q: How do you handle background noise?**
A: Using Google Speech Recognition which has built-in noise cancellation. Can be improved with pre-processing.

**Q: What if the job type is not in your list?**
A: We use fuzzy matching and accept reasonable variations. System can learn new jobs over time.

**Q: How accurate is the validation?**
A: 90%+ accuracy on test data. See VALIDATION_SYSTEM.md for details.

**Q: Can this work offline?**
A: Currently needs internet for speech recognition. Can be made offline with Vosk or Whisper.

---

## 🚀 Next Steps After Hackathon

1. Add more regional languages
2. Integrate with job boards
3. Add employer dashboard
4. Mobile app (React Native)
5. Offline mode with local models
6. Analytics dashboard

---

**Good luck with the demo! 🎉**




