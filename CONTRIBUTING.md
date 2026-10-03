# Contributing

Thanks for your interest in improving this project!

## Local setup

1. Copy `.env.example` to `.env` and adjust values.
2. Start the stack: `docker compose up --build`
3. Backend only: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
4. Frontend only: `cd frontend && npm install && npm run dev`

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
```

## Pull requests

* Branch from `main` and keep PRs focused on one change.
* Link the issue your PR addresses (e.g. `Closes #12`).
* CI must pass (backend import check + frontend build).
