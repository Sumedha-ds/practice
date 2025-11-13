# Job Management API

This document summarizes the available HTTP endpoints exposed by the Job Management service.  
All endpoints are served from the FastAPI application in `app/main.py`.

---

## Service Metadata

- **Base URL (local):** `http://localhost:8000`
- **API Version Prefix:** `/api/v1`
- **OpenAPI Docs:** `http://localhost:8000/docs`
- **JSON Schema Docs:** `http://localhost:8000/redoc`

---

## Health & Root

### `GET /`
- **Purpose:** Basic connectivity check with project metadata.
- **Response Body:**
  ```json
  {
    "message": "Job Management API",
    "version": "1.0.0",
    "docs": "/docs"
  }
  ```

### `GET /health`
- **Purpose:** Lightweight health probe for infrastructure monitoring.
- **Response Body:**
  ```json
  {
    "status": "healthy"
  }
  ```

---

## Jobs

### `GET /api/v1/jobs`
- **Description:** Retrieve all jobs, optionally filtered by city, and enriched with user-specific status and audio metadata.
- **Query Parameters:**
  | Name | Type | Description |
  |------|------|-------------|
  | `city` | `string` | Optional city filter (exact match). |
  | `userId` | `integer` | Optional user identifier to include individualized job status. |

- **Response Model:** `JobListResponse`

  ```json
  {
    "jobs": [
      {
        "jobId": 1,
        "wage": 18000.0,
        "city": "Pune",
        "jobTitle": "Carpenter",
        "gender": "Any",
        "audioScript": "नमस्ते ...",
        "audio": "data:audio/mp3;base64,...",
        "jobStatus": "pending"
      }
    ]
  }
  ```

### `POST /api/v1/jobs/action`
- **Description:** Apply for or reject a job on behalf of a user.
- **Request Model:** `JobAction`

  ```json
  {
    "jobId": "1",
    "userId": "1",
    "action": "apply"
  }
  ```

- **Response Model:** `MessageResponse`

  ```json
  {
    "message": "Job applied successfully"
  }
  ```

---

## Schemas

| Model | Fields | Notes |
|-------|--------|-------|
| `JobAction` | `jobId: str \| int`, `userId: str \| int`, `action: str` | `action` must be `"apply"` or `"reject"`. |
| `JobResponse` | `jobId: int`, `wage: float`, `city: str`, `jobTitle: str`, `gender: str`, `audioScript: str`, `audio: str`, `jobStatus: str` | `audio` contains a Base64-encoded MP3 `data:` URI. |
| `JobListResponse` | `jobs: list[JobResponse]` | Aggregates job responses. |
| `MessageResponse` | `message: str` | Generic success acknowledgement. |

Each schema is defined under `app/schemas/` and is fully documented in the generated OpenAPI specification exposed at `/docs`.

---

## Notes

- All endpoints currently allow any origin (`*`) via CORS. Update `Settings.allow_origins` in `app/core/config.py` for production.
- Database configuration and session management are defined in `app/db/session.py`, with models in `app/models/`.


