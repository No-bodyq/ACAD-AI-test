# Acad AI — Mini Assessment Engine

This repository contains a Django + DRF mini assessment engine used for backend testing. It provides endpoints for Exams, Questions, Submissions, and a modular grading system (mock grader by default; optional Gemini LLM integration).

## Quick setup (Windows, Git Bash / bash)

1. Clone repository and change into project root (this repo already in workspace):

   ```bash
   cd <assessment_engine>
   ```

2. Create and activate a virtual environment (if not already):

   ```bash
   python -m venv venv
   source venv/Scripts/activate
   ```

3. Install required packages (recommended):

   pip install -U pip
   pip install django djangorestframework djangorestframework-authtoken

   # Optional for Gemini grading

   pip install google-generativeai

4. Apply migrations and create a superuser:

   python manage.py migrate
   python manage.py createsuperuser

5. (Optional) Create a token for a user via management command:

   python manage.py drf_create_token <username>

   If you prefer, you can POST to `/api-token-auth/` if you add the following to your project `urls.py`:

   ```py
   from rest_framework.authtoken.views import obtain_auth_token
   path('api-token-auth/', obtain_auth_token),
   ```

6. Run the server:

   python manage.py runserver

## Environment variables

- `GRADING_STRATEGY` — `mock` (default) or `gemini` to enable GeminiGrader.
- `GOOGLE_API_KEY` — required when `GRADING_STRATEGY=gemini`.

Do NOT commit API keys or `.env` to source control. Use a `.env` file or CI secret store.

## API Overview

Base URL: http://127.0.0.1:8000 (adjust if running elsewhere)

Endpoints (registered on the root router `/api/`):

- `GET /api/users/` — list users
- `POST /api/users/` — create user (staff only)
- `GET /api/exams/` — list exams (questions nested)
- `GET /api/exams/{id}/` — exam detail
- `GET /api/questions/` — list questions
- `POST /api/questions/` — create question (staff only)
- `GET /api/submissions/` — list submissions (students see their own; staff sees all)
- `POST /api/submissions/` — create a submission (authenticated users)

Authentication: Token authentication is supported. Add header `Authorization: Token <token>`.

### Submissions: payload formats

You can reference questions in `answers`by the question's order index (1-based) as shown in the exam object.

Example (by question id):

Example (by question order index):

```json
{
  "exam": 3,
  "answers": [
    { "question": 1, "selected_choice": "B" },
    { "question": 2, "answer_text": "Explanation..." }
  ]
}
```

Notes on validation

- MCQ questions require `selected_choice` and the value must match one of the question's choice keys.
- Text questions require `answer_text`.
- Students can currently make only one submission per exam (enforced by DB unique constraint). Staff users can create multiple submissions.

## Gemini LLM grading (optional)

To use Gemini for text grading:

1. Set `GRADING_STRATEGY=gemini` in your environment.
2. Set `GOOGLE_API_KEY` to a valid key.
3. Install `google-generativeai` package.

The grader will call Gemini synchronously and return `feedback` per answer in the submission response. For production workloads or to avoid blocking requests, consider async grading (Celery) instead.

## Postman

A Postman collection `postman_collection.json` is included in the repo with example requests. Import it into Postman and set an environment with:

- `base_url` = http://127.0.0.1:8000
- `token` = <your_token>

Then use the requests:

- `GET {{base_url}}/api/exams/` — inspect question ids and order
- `POST {{base_url}}/api/submissions/` — create a submission (add Authorization header)

## Troubleshooting

- 401 Unauthorized: ensure header `Authorization: Token <token>` is present.
- 400 Bad Request: check error fields (e.g., `answers[0]` indicates index of problematic answer). Use exam details to confirm question ids/order.
- 500 errors: check the Django runserver console for tracebacks.

## Development notes

- Questions choices are expected to be stored as JSON (list of dicts with `key` and `text` fields is recommended).
- The project includes a `grader` module that supports `MockGrader` and `GeminiGrader`.
