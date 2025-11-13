# FastAPI Job Management Backend - Setup Guide

## Quick Start

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Seed the Database**:
```bash
python app/seed.py
```

3. **Run the Server**:
```bash
python run_fastapi.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Access the API**:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI application entry point
├── database.py          # SQLAlchemy database configuration
├── seed.py              # Database seed script
├── models/              # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── job.py          # Job model
│   ├── user.py         # User model
│   └── user_job.py     # UserJob relationship model
├── schemas/             # Pydantic request/response schemas
│   ├── __init__.py
│   ├── job.py          # Job-related schemas
│   └── user.py         # User-related schemas
└── routes/              # API route handlers
    ├── __init__.py
    └── jobs.py         # Job-related routes
```

## Database Schema

### Jobs Table
- `id` (Integer, Primary Key)
- `jobTitle` (String)
- `wage` (Float)
- `city` (String)
- `gender` (String)
- `audioScript` (Text) - base64-encoded MP3 or file path
- `status` (String) - "open" or "closed"

### Users Table
- `id` (Integer, Primary Key)
- `name` (String)
- `city` (String)

### User Jobs Table
- `userId` (Integer, Foreign Key, Primary Key)
- `jobId` (Integer, Foreign Key, Primary Key)
- `status` (String) - "applied", "rejected", etc.

## API Endpoints

### POST /job/action
Apply or reject a job for a user.

**Request Body**:
```json
{
  "jobId": "1",
  "userId": "1",
  "action": "apply"
}
```

**Response**:
```json
{
  "message": "Job applied successfully"
}
```

### GET /jobs
Get all jobs with optional filtering.

**Query Parameters**:
- `city` (optional): Filter jobs by city
- `userId` (optional): User ID to determine job status

**Response**:
```json
{
  "jobs": [
    {
      "jobId": 1,
      "wage": 120000.0,
      "city": "New York",
      "jobTitle": "Software Engineer",
      "gender": "Any",
      "audioScript": "data:audio/mp3;base64,...",
      "jobStatus": "applied"
    }
  ]
}
```

## Testing

### Test Apply Job
```bash
curl -X POST "http://localhost:8000/job/action" \
  -H "Content-Type: application/json" \
  -d '{
    "jobId": "1",
    "userId": "1",
    "action": "apply"
  }'
```

### Test Get All Jobs
```bash
curl "http://localhost:8000/jobs"
```

### Test Get Jobs by City
```bash
curl "http://localhost:8000/jobs?city=New York"
```

### Test Get Jobs with User Status
```bash
curl "http://localhost:8000/jobs?userId=1"
```

## Seed Data

The seed script creates:
- 5 users (John Doe, Jane Smith, Bob Johnson, Alice Williams, Charlie Brown)
- 8 jobs (Software Engineer, Data Scientist, Product Manager, UX Designer, DevOps Engineer, Marketing Manager, Sales Representative, Accountant)
- 6 user-job relationships (examples of applied/rejected statuses)

## Notes

- Database file (`jobs.db`) is created automatically
- Job status can be: `applied`, `rejected`, `pending`, or `closed`
- Closed jobs cannot be applied to or rejected
- If `userId` is not provided in GET /jobs, all jobs show status as "pending"
- Job status is determined from the `user_jobs` table
- Closed jobs always show status as "closed" regardless of user actions

