# Requirements Checklist for Vercel Deployment

## ✅ Pre-Deployment Requirements

### 1. System Requirements
- [ ] **Node.js** installed (v14 or higher)
  - Check: `node --version`
  - Install: [nodejs.org](https://nodejs.org/)
- [ ] **npm** installed (comes with Node.js)
  - Check: `npm --version`
- [ ] **Python** 3.9+ (Vercel supports Python 3.9, 3.10, 3.11)
  - Check: `python --version`
  - Note: Vercel uses Python 3.9 by default

### 2. Vercel Account
- [ ] **Vercel account** created
  - Sign up: [vercel.com/signup](https://vercel.com/signup)
  - Free tier available

### 3. Vercel CLI
- [ ] **Vercel CLI** installed globally
  - Install: `npm install -g vercel`
  - Check: `vercel --version`
- [ ] **Logged in** to Vercel
  - Login: `vercel login`

### 4. Project Files
- [x] `api/index.py` - FastAPI application ✅
- [x] `vercel.json` - Vercel configuration ✅
- [x] `requirements-vercel.txt` - Web dependencies ✅
- [x] `deploy.sh` - Deployment script ✅
- [x] `.vercelignore` - Files to exclude ✅

### 5. Dependencies Check

#### ✅ Included in requirements-vercel.txt:
- [x] `fastapi` - Web framework
- [x] `uvicorn` - ASGI server
- [x] `pydantic` - Data validation
- [x] `python-multipart` - File uploads
- [x] `SpeechRecognition` - Speech recognition
- [x] `gTTS` - Text-to-speech
- [x] `translate` - Translation library
- [x] `requests` - HTTP requests
- [x] `audioop-lts` - Audio operations (Python 3.13 compatibility)

#### ❌ Removed (not compatible with serverless):
- [x] `PyQt5` - Desktop GUI framework (removed)
- [x] `PyAudio` - Microphone access (removed)

### 6. Code Compatibility

#### ✅ Serverless-Compatible Features:
- [x] FastAPI web framework
- [x] File upload handling
- [x] Audio file processing (uploaded files)
- [x] Text translation
- [x] Text-to-speech generation
- [x] SQLite database (using `/tmp` directory)

#### ⚠️ Limitations:
- [ ] **Microphone access**: Not available (users must upload audio files)
- [ ] **Persistent storage**: SQLite in `/tmp` is temporary
- [ ] **File size limits**: 4.5MB for Hobby plan, 50MB for Pro
- [ ] **Execution timeout**: 10s (Hobby) or 60s (Pro)

### 7. Environment Variables
- [x] `DB_PATH` - Set to `/tmp/transcripts.db` in vercel.json
- [ ] Additional variables (if needed):
  - API keys
  - Database connection strings
  - Other secrets

### 8. Git Repository (Optional but Recommended)
- [ ] Code pushed to Git repository
  - GitHub
  - GitLab
  - Bitbucket
- [ ] Repository connected to Vercel (for auto-deploy)

## 📋 Deployment Steps Checklist

### Step 1: Preparation
- [ ] Review `DEPLOYMENT.md` or `QUICK_START.md`
- [ ] Ensure all files are in place
- [ ] Test locally (optional but recommended)

### Step 2: Requirements File
- [ ] Copy `requirements-vercel.txt` to `requirements.txt`
  - Or use `./deploy.sh` script (handles automatically)

### Step 3: Deploy
- [ ] Run `vercel login` (if not logged in)
- [ ] Run `./deploy.sh` or `vercel`
- [ ] Follow prompts
- [ ] Note the deployment URL

### Step 4: Test
- [ ] Test health check endpoint: `GET /`
- [ ] Test translation endpoint: `POST /api/translate`
- [ ] Test other endpoints as needed

### Step 5: Production
- [ ] Deploy to production: `./deploy.sh --prod` or `vercel --prod`
- [ ] Verify production URL
- [ ] Test all endpoints in production

## 🔍 Post-Deployment Checks

### API Endpoints
- [ ] `/` - Health check returns 200
- [ ] `/api/translate` - Translation works
- [ ] `/api/transcribe` - Audio transcription works
- [ ] `/api/text-to-speech` - TTS generation works
- [ ] `/api/transcribe-and-translate` - Full pipeline works
- [ ] `/api/send-otp` - OTP generation works
- [ ] `/api/verify-otp` - OTP verification works
- [ ] `/api/onboard-worker` - Worker onboarding works
- [ ] `/api/workers` - Worker list returns data
- [ ] `/api/transcripts` - Transcript list returns data

### Performance
- [ ] Response times are acceptable (< 5s for most endpoints)
- [ ] No timeout errors
- [ ] File uploads work within size limits

### Error Handling
- [ ] Invalid requests return appropriate error codes
- [ ] Error messages are clear
- [ ] CORS is configured correctly

## 🚨 Common Issues & Solutions

### Issue: "Module not found"
- **Check**: All dependencies in `requirements-vercel.txt`
- **Solution**: Ensure `requirements.txt` matches `requirements-vercel.txt`

### Issue: "Function timeout"
- **Check**: Long-running operations
- **Solution**: Optimize code or upgrade to Pro plan

### Issue: "Database write errors"
- **Check**: Using `/tmp` directory
- **Solution**: Ensure DB_PATH is set to `/tmp/transcripts.db`

### Issue: "CORS errors"
- **Check**: CORS middleware configuration
- **Solution**: Update `allow_origins` in `api/index.py`

### Issue: "File too large"
- **Check**: File size limits
- **Solution**: Compress files or use external storage

## 📊 Recommended Next Steps

### For Production:
1. [ ] Set up external database (PostgreSQL, MongoDB)
2. [ ] Configure environment variables
3. [ ] Set up custom domain
4. [ ] Enable monitoring and logging
5. [ ] Set up CI/CD pipeline
6. [ ] Configure rate limiting
7. [ ] Add authentication/authorization
8. [ ] Set up error tracking (Sentry, etc.)

### For Development:
1. [ ] Create frontend application
2. [ ] Set up local development environment
3. [ ] Add API documentation (Swagger/OpenAPI)
4. [ ] Write tests
5. [ ] Set up local database

## 📚 Documentation Files

- [x] `DEPLOYMENT.md` - Full deployment guide
- [x] `QUICK_START.md` - Quick reference
- [x] `REQUIREMENTS_CHECKLIST.md` - This file
- [x] `README.md` - Original project README

## ✅ Final Checklist

Before going to production:
- [ ] All endpoints tested
- [ ] Error handling verified
- [ ] Performance acceptable
- [ ] Security reviewed
- [ ] Documentation complete
- [ ] Monitoring set up
- [ ] Backup strategy in place

---

**Last Updated**: Check file modification date
**Status**: Ready for deployment ✅

