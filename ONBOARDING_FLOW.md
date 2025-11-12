# Onboarding Flow - How It Works

## Overview
The onboarding process asks 9 questions one by one (serially) to collect worker information.

## Complete Flow Diagram

```
1. User enters phone number
   ↓
2. Send OTP API
   ↓
3. Verify OTP API
   ↓
4. Check profile_exists in response
   ↓
   ├─→ If profile_exists = true
   │   → Show "Onboarding completed! Login successful."
   │   → User can access dashboard
   │
   └─→ If profile_exists = false
       → Start onboarding flow
       ↓
5. Get Questions API (get all questions)
   ↓
6. Frontend displays Question 1
   ↓
7. User answers Question 1
   ↓
8. Frontend stores answer locally
   ↓
9. Frontend displays Question 2
   ↓
10. User answers Question 2
   ↓
... (repeat for all 9 questions)
   ↓
11. User answers Question 9 (last question)
   ↓
12. Frontend calls Complete Onboarding API with ALL answers
   ↓
13. Backend saves profile and sets profile_created = 1
   ↓
14. User can now login and access dashboard
```

## Detailed Step-by-Step Flow

### Step 1: Phone Number & OTP Verification

**1.1 Send OTP**
```
POST /api/auth/send-otp
Body: {"phone_number": "1234567890"}
Response: {"success": true, "otp": "123456"}
```

**1.2 Verify OTP**
```
POST /api/auth/verify-otp
Body: {"phone_number": "1234567890", "otp": "123456"}
Response: {
  "success": true,
  "profile_exists": false,  // or true if already onboarded
  "token": "token_1234567890_1234"
}
```

### Step 2: Check Profile Status

**If `profile_exists = true`:**
- Show message: "Onboarding completed! Login successful."
- User can access dashboard immediately
- **Flow ends here**

**If `profile_exists = false`:**
- Show message: "No profile found. Starting onboarding..."
- Proceed to Step 3

### Step 3: Get Questions List

```
GET /api/onboarding/questions?language=en
Response: {
  "success": true,
  "questions": [
    {"key": "name", "en": "What is your name?", "hi": "..."},
    {"key": "skill", "en": "What is your skill?", "hi": "..."},
    ...
  ]
}
```

### Step 4: Serial Question Flow (Frontend Implementation)

**Frontend Logic:**
```javascript
// Pseudo-code for frontend
const questions = response.questions; // Array of 9 questions
let currentQuestionIndex = 0;
let answers = {}; // Store answers as user progresses

function showNextQuestion() {
  if (currentQuestionIndex < questions.length) {
    const question = questions[currentQuestionIndex];
    // Display question to user
    // Wait for user input
    // Store answer in answers object
    answers[question.key] = userInput;
    currentQuestionIndex++;
    showNextQuestion(); // Recursive call
  } else {
    // All questions answered
    completeOnboarding();
  }
}

function completeOnboarding() {
  // Call API with all answers
  POST /api/onboarding/complete
  Body: {
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
}
```

### Step 5: Complete Onboarding

```
POST /api/onboarding/complete
Headers: {
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json"
}
Body: {
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
Response: {
  "success": true,
  "message": "Onboarding complete and saved",
  "worker_id": 123,
  "phone_number": "1234567890"
}
```

## Questions Order (Serial Flow)

The questions are asked in this exact order:

1. **Name** - "What is your name?"
2. **Skill** - "What is your skill? (eg: plumber, painter)"
3. **Education** - "What is your education level?"
4. **Age** - "What is your age?"
5. **Sex** - "What is your sex? (male/female)"
6. **Experience** - "How many years of experience?"
7. **Location** - "Which city or village are you from?"
8. **Wage Expected** - "What is your expected daily wage?"
9. **Languages Known** - "Which languages do you know?"

## Frontend Implementation Example

### React/Next.js Example:

```jsx
import { useState, useEffect } from 'react';

function OnboardingFlow() {
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  // Step 1: Get questions on component mount
  useEffect(() => {
    fetch('/api/onboarding/questions?language=en')
      .then(res => res.json())
      .then(data => setQuestions(data.questions));
  }, []);

  const handleNext = () => {
    const currentQuestion = questions[currentIndex];
    
    // Save current answer
    setAnswers({
      ...answers,
      [currentQuestion.key]: currentAnswer
    });

    // Move to next question or complete
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setCurrentAnswer(''); // Clear input
    } else {
      // All questions answered - complete onboarding
      completeOnboarding();
    }
  };

  const completeOnboarding = async () => {
    setLoading(true);
    const token = localStorage.getItem('token');
    
    try {
      const response = await fetch('/api/onboarding/complete', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ answers })
      });
      
      const data = await response.json();
      if (data.success) {
        // Redirect to dashboard
        window.location.href = '/dashboard';
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  if (questions.length === 0) return <div>Loading...</div>;

  const currentQuestion = questions[currentIndex];
  const isLastQuestion = currentIndex === questions.length - 1;

  return (
    <div className="onboarding-container">
      <h2>Question {currentIndex + 1} of {questions.length}</h2>
      
      <div className="question">
        <h3>{currentQuestion.en}</h3>
        <input
          type="text"
          value={currentAnswer}
          onChange={(e) => setCurrentAnswer(e.target.value)}
          placeholder="Enter your answer"
        />
      </div>

      <div className="progress-bar">
        <div style={{ width: `${((currentIndex + 1) / questions.length) * 100}%` }} />
      </div>

      <button 
        onClick={handleNext}
        disabled={!currentAnswer || loading}
      >
        {isLastQuestion ? 'Complete Onboarding' : 'Next Question'}
      </button>
    </div>
  );
}
```

## Important Points

1. **Serial Flow**: Questions are asked ONE AT A TIME, not all at once
2. **Progress Tracking**: Frontend should show progress (e.g., "Question 3 of 9")
3. **Answer Storage**: Store answers locally until all questions are answered
4. **Single API Call**: Only call `/api/onboarding/complete` ONCE with all answers
5. **Token Required**: Complete onboarding requires authentication token from verify-otp
6. **Validation**: Frontend can validate answers before allowing "Next"
7. **Back Navigation**: Optional - allow users to go back and edit previous answers

## Alternative: Progressive Save (Optional Enhancement)

If you want to save answers as user progresses (not recommended for simple flow):

```
POST /api/onboarding/answer
Body: {
  "phone_number": "1234567890",
  "question_key": "name",
  "answer": "John Doe"
}
```

But the current implementation uses **batch save** - all answers saved at once when onboarding is complete.

