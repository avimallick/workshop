# Groq LangChain FastAPI Workshop Service

## What this is
A minimal FastAPI microservice that calls GroqCloud through LangChain. Students only edit one file (`prompts.py`) to change the assistant persona. It runs locally with Uvicorn and deploys to Hugging Face Spaces as a Docker Space with Swagger at `/docs`.


Something


## API contract
**POST /chat**

Request:
```json
{ "message": "string" }
```

Response:
```json
{ "answer": "string" }
```

**GET /health**

Response:
```json
{ "status": "ok" }
```

## Run locally
1) Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Set your Groq API key
```bash
export GROQ_API_KEY=your_key_here
```

Optional: set a service API key to protect `/chat`
```bash
export SERVICE_API_KEY=my_secret
```

4) Run the server
```bash
uvicorn main:app --reload
```

5) Open Swagger UI
```text
http://127.0.0.1:8000/docs
```

## Curl examples
Basic call:
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello!"}'
```

With API key protection enabled:
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: my_secret" \
  -d '{"message":"Hello!"}'
```

## Prompt Twist
Only edit `prompts.py` to change the assistant persona. Do not modify any other file.

## Deploy to Hugging Face Spaces (Docker)
1) Create a new Space on Hugging Face.
2) Choose **Docker** as the Space type.
3) Connect your forked repo.
4) Add secrets in the Space settings:
   - `GROQ_API_KEY` (required)
   - `SERVICE_API_KEY` (optional)
5) The Space builds automatically. When it is ready, open:
```
https://<space>.hf.space/docs
```

## Troubleshooting
- **Missing GROQ_API_KEY**: Set the environment variable locally or as a Space secret.
- **Build failures**: Check the build logs for missing dependencies or syntax errors.
- **Wrong port**: The Dockerfile exposes and runs on port 7860 as required by Spaces.

## Suggested student challenges
- Change the persona in `prompts.py` to become a coach, detective, or poet.
- Add a second endpoint that transforms text (keep `/chat` unchanged).
- Add request validation rules (e.g., minimum length) and user-friendly errors.
- Log response time and show it in the output.
- Add a simple rate limit or per-IP counter.
