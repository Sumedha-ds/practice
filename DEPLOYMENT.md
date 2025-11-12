# Deployment Guide: Python Backend on Vercel

This guide will walk you through deploying your Python backend API on Vercel.

## ⚠️ Important Notes

### What Changed
- **Original**: PyQt5 desktop application with microphone access
- **Deployed**: FastAPI web API that accepts audio file uploads
- **Database**: SQLite (note: Vercel has read-only filesystem, so database writes may be limited)

### Limitations on Vercel
1. **No Microphone Access**: Serverless functions can't access client microphones. Users must upload audio files.
2. **Read-Only Filesystem**: SQLite writes to `/tmp` directory (temporary, may be cleared)
3. **No Persistent Storage**: Consider using external database (PostgreSQL, MongoDB) for production
4. **Function Timeout**: Vercel has execution time limits (10s for Hobby, 60s for Pro)

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install globally
   ```bash
   npm install -g vercel
   ```
3. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, or Bitbucket)

## Step-by-Step Deployment

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Login to Vercel

```bash
vercel login
```

This will open a browser window for authentication.

### Step 3: Prepare Your Project

1. **Use the correct requirements file**:
   - Vercel automatically looks for `requirements.txt` in the root directory
   - You have two options:
     - **Option A (Recommended)**: Temporarily rename `requirements-vercel.txt` to `requirements.txt` before deployment
     - **Option B**: Copy `requirements-vercel.txt` to `requirements.txt`:
       ```bash
       cp requirements-vercel.txt requirements.txt
       ```
   - The `requirements-vercel.txt` excludes PyQt5 and PyAudio which don't work in serverless

2. **Verify your project structure**:
   ```
   your-project/
   ├── api/
   │   └── index.py          # FastAPI application
   ├── vercel.json           # Vercel configuration
   ├── requirements-vercel.txt  # Dependencies for Vercel
   └── .gitignore
   ```

### Step 4: Deploy to Vercel

From your project root directory:

```bash
vercel
```

Follow the prompts:
- **Set up and deploy?** → Yes
- **Which scope?** → Select your account/team
- **Link to existing project?** → No (for first deployment)
- **Project name?** → Enter a name or press Enter for default
- **Directory?** → Press Enter (uses current directory)
- **Override settings?** → No (for first deployment)

### Step 5: Production Deployment

After initial deployment, deploy to production:

```bash
vercel --prod
```

## Alternative: Deploy via GitHub

1. **Push your code to GitHub**
2. **Go to [vercel.com/dashboard](https://vercel.com/dashboard)**
3. **Click "Add New Project"**
4. **Import your GitHub repository**
5. **Configure project**:
   - Framework Preset: Other
   - Root Directory: ./
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
6. **Environment Variables** (if needed):
   - Add any required environment variables
7. **Click "Deploy"**

## Project Configuration

### vercel.json

The `vercel.json` file configures:
- Python runtime for `api/index.py`
- Routing to handle all requests
- Environment variables

### API Endpoints

Your API will be available at:
- `https://your-project.vercel.app/` - Health check
- `https://your-project.vercel.app/api/transcribe` - Transcribe audio
- `https://your-project.vercel.app/api/translate` - Translate text
- `https://your-project.vercel.app/api/text-to-speech` - Generate speech
- `https://your-project.vercel.app/api/transcribe-and-translate` - Full pipeline
- `https://your-project.vercel.app/api/send-otp` - Send OTP
- `https://your-project.vercel.app/api/verify-otp` - Verify OTP
- `https://your-project.vercel.app/api/onboard-worker` - Onboard worker
- `https://your-project.vercel.app/api/workers` - Get all workers
- `https://your-project.vercel.app/api/transcripts` - Get transcripts

## Testing the Deployment

### 1. Health Check

```bash
curl https://your-project.vercel.app/
```

Expected response:
```json
{"message": "Voice Transcriber API is running", "status": "ok"}
```

### 2. Test Translation

```bash
curl -X POST https://your-project.vercel.app/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "src_lang": "en",
    "tgt_lang": "hi"
  }'
```

### 3. Test Audio Transcription

```bash
curl -X POST https://your-project.vercel.app/api/transcribe \
  -F "audio_file=@path/to/audio.wav" \
  -F "language=en-US"
```

## Environment Variables

If you need to set environment variables:

1. **Via CLI**:
   ```bash
   vercel env add DB_PATH
   ```

2. **Via Dashboard**:
   - Go to your project on Vercel
   - Settings → Environment Variables
   - Add variables for Production, Preview, and Development

## Database Considerations

### Current Setup (SQLite in /tmp)
- ⚠️ **Temporary**: Data may be lost between function invocations
- ✅ **Simple**: No external dependencies
- ❌ **Not recommended for production**

### Recommended: External Database

For production, use:
- **PostgreSQL**: Vercel Postgres, Supabase, or Railway
- **MongoDB**: MongoDB Atlas
- **Other**: Any cloud database service

Update `api/index.py` to use your database connection string:

```python
import os
import psycopg2  # For PostgreSQL

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    return psycopg2.connect(DATABASE_URL)
```

## Troubleshooting

### Issue: "Module not found"
**Solution**: Ensure all dependencies are in `requirements-vercel.txt`

### Issue: "Function timeout"
**Solution**: 
- Optimize your code
- Consider upgrading to Vercel Pro (60s timeout)
- Break long operations into smaller functions

### Issue: "Database write errors"
**Solution**: 
- Use `/tmp` directory for temporary files
- Consider external database for persistent storage

### Issue: "CORS errors"
**Solution**: Update CORS settings in `api/index.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specific domain
    ...
)
```

### Issue: "Audio file too large"
**Solution**: 
- Vercel has payload size limits (4.5MB for Hobby)
- Compress audio files before upload
- Consider using external storage (S3, Cloudinary) for large files

## Monitoring and Logs

View logs in Vercel Dashboard:
1. Go to your project
2. Click "Deployments"
3. Select a deployment
4. Click "Functions" tab
5. View logs for each function

Or via CLI:
```bash
vercel logs
```

## Updating Your Deployment

After making changes:

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

Or push to your connected Git repository - Vercel will auto-deploy.

## Cost Considerations

- **Hobby Plan**: Free tier with limitations
- **Pro Plan**: $20/month for better performance and limits
- Check [Vercel Pricing](https://vercel.com/pricing) for details

## Next Steps

1. ✅ Deploy to Vercel
2. ✅ Test all endpoints
3. 🔄 Set up external database (recommended)
4. 🔄 Create frontend application
5. 🔄 Set up CI/CD pipeline
6. 🔄 Configure custom domain

## Support

- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vercel Community](https://github.com/vercel/vercel/discussions)

