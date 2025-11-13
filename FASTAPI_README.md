# FastAPI Job Management Backend

A FastAPI backend application for managing jobs, users, and job applications.

## Features

- **Apply/Reject Job API**: Apply or reject jobs for users
- **Get All Jobs API**: Fetch all jobs with optional city filtering and user-specific job status
- **Database Schema**: SQLite database with jobs, users, and user_jobs tables
- **RESTful API**: Clean REST API with proper HTTP status codes and error handling
- **Pydantic Validation**: Request/response validation using Pydantic models
- **SQLAlchemy ORM**: Database operations using SQLAlchemy ORM

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Seed the database with test data:
```bash
python app/seed.py
```

## Running the Application

Run the FastAPI server:
```bash
python run_fastapi.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive API Docs (Swagger): http://localhost:8000/docs
- Alternative API Docs (ReDoc): http://localhost:8000/redoc

## API Endpoints

### 1. Apply/Reject Job

**Endpoint**: `POST /job/action`

**Payload**:
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

**Error Responses**:
- `400`: Invalid request (invalid jobId, userId, or action)
- `404`: Job or user not found
- `400`: Cannot apply to a closed job

### 2. Get All Jobs

**Endpoint**: `GET /jobs`

**Query Parameters**:
- `city` (optional): Filter jobs by city
- `userId` (optional): User ID to determine job status (applied/rejected/pending)

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
      "audioScript": "data:audio/mp3;base64,SGVsbG8gV29ybGQ=",
      "jobStatus": "applied"
    }
  ]
}
```

**Example Requests**:
- Get all jobs: `GET /jobs`
- Get jobs in a specific city: `GET /jobs?city=New York`
- Get jobs with user status: `GET /jobs?userId=1`
- Get jobs in a city with user status: `GET /jobs?city=New York&userId=1`

## Database Schema

### Jobs Table
- `id`: Integer (Primary Key)
- `jobTitle`: String
- `wage`: Float
- `city`: String
- `gender`: String
- `audioScript`: Text (base64-encoded MP3 or file path)
- `status`: String (open/closed)

### Users Table
- `id`: Integer (Primary Key)
- `name`: String
- `city`: String

### User Jobs Table
- `userId`: Integer (Foreign Key, Primary Key)
- `jobId`: Integer (Foreign Key, Primary Key)
- `status`: String (applied, rejected, etc.)

## Project Structure

```
app/
├── __init__.py
├── main.py              # FastAPI application
├── database.py          # Database configuration
├── seed.py              # Seed data script
├── models/              # SQLAlchemy models
│   ├── __init__.py
│   ├── job.py
│   ├── user.py
│   └── user_job.py
├── schemas/             # Pydantic schemas
│   ├── __init__.py
│   ├── job.py
│   └── user.py
└── routes/              # API routes
    ├── __init__.py
    └── jobs.py
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

## Notes

- The database file (`jobs.db`) will be created automatically when you run the application
- Seed data includes 5 users and 8 jobs for testing
- Job status can be: `applied`, `rejected`, `pending`, or `closed`
- Closed jobs will always show status as "closed" regardless of user actions
- If `userId` is not provided in GET /jobs, all jobs will show status as "pending"

