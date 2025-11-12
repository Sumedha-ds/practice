# Quick Start: Deploy to Vercel

## Prerequisites Checklist

- [ ] Node.js installed (for Vercel CLI)
- [ ] Vercel account created
- [ ] Git repository set up

## Quick Deployment (5 minutes)

### Option 1: Using Deployment Script (Recommended)

```bash
# Make script executable (first time only)
chmod +x deploy.sh

# Deploy to preview
./deploy.sh

# Deploy to production
./deploy.sh --prod
```

### Option 2: Manual Deployment

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login**
   ```bash
   vercel login
   ```

3. **Prepare requirements file**
   ```bash
   cp requirements-vercel.txt requirements.txt
   ```

4. **Deploy**
   ```bash
   vercel              # Preview
   vercel --prod       # Production
   ```

## What Was Changed?

### ✅ Created
- `api/index.py` - FastAPI web API server
- `vercel.json` - Vercel configuration
- `requirements-vercel.txt` - Web dependencies (no PyQt5/PyAudio)
- `DEPLOYMENT.md` - Full deployment guide

### ⚠️ Important Changes
- **No PyQt5**: Desktop GUI removed (can't run on serverless)
- **No PyAudio**: Microphone access removed (users upload audio files)
- **Database**: Uses `/tmp` directory (temporary storage)

## API Endpoints

Base URL: `https://your-project.vercel.app`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/transcribe` | POST | Transcribe audio file |
| `/api/translate` | POST | Translate text |
| `/api/text-to-speech` | POST | Convert text to speech |
| `/api/transcribe-and-translate` | POST | Full pipeline |
| `/api/send-otp` | POST | Send OTP |
| `/api/verify-otp` | POST | Verify OTP |
| `/api/onboard-worker` | POST | Save worker data |
| `/api/workers` | GET | Get all workers |
| `/api/transcripts` | GET | Get transcripts |

## Test Your Deployment

```bash
# Health check
curl https://your-project.vercel.app/

# Translate text
curl -X POST https://your-project.vercel.app/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello", "src_lang": "en", "tgt_lang": "hi"}'
```

## Next Steps

1. Read `DEPLOYMENT.md` for detailed instructions
2. Set up external database (recommended for production)
3. Create frontend application
4. Configure custom domain

## Need Help?

See `DEPLOYMENT.md` for:
- Detailed step-by-step guide
- Troubleshooting
- Database setup
- Environment variables
- Monitoring and logs

