# How to Run the API Server

## Step 1: Activate Virtual Environment
```bash
cd /Users/dealshare/Main
source venv/bin/activate
```

## Step 2: Install Dependencies (if not already installed)
```bash
pip install -r requirements.txt
```

## Step 3: Run the API Server
```bash
python api_server.py
```

The server will start on: **http://localhost:5000**

---

## Quick Start (All in One)
```bash
cd /Users/dealshare/Main && source venv/bin/activate && python api_server.py
```

---

## Test the API

### Using curl:

**Health Check:**
```bash
curl http://localhost:5000/api/health
```

**Send OTP:**
```bash
curl -X POST http://localhost:5000/api/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "1234567890"}'
```

**Verify OTP:**
```bash
curl -X POST http://localhost:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "1234567890", "otp": "123456"}'
```

### Using Postman:
1. Open Postman
2. Base URL: `http://localhost:5000/api`
3. Test endpoints as documented in `API_DOCUMENTATION.md`

---

## Stop the Server
Press `Ctrl + C` in the terminal where the server is running.

