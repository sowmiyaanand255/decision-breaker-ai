# Decision Breaker AI

## 🚀 Live Demo
[Open Decision Breaker AI](https://decision-breaker-ai.onrender.com)

Decision Breaker AI is an AI-powered critical decision and risk analysis web application.

## Core idea
Instead of simply agreeing with a user's plan, the system challenges it by identifying:
- hidden assumptions
- blind spots
- risks
- counterarguments
- alternatives
- evidence that should be collected before committing

The signature feature is **Break My Decision**, which deliberately constructs the strongest practical case against the user's plan.

## Stack
- Python
- Flask
- HTML/CSS/JavaScript
- SQLite
- OpenAI Responses API (optional; demo fallback is included)
- Git/GitHub

## Run locally
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# or: cp .env.example .env
python app.py
```

Open https://decision-breaker-ai.onrender.com

### AI mode
Add your API key to `.env`:
`OPENAI_API_KEY=...`

The application uses the OpenAI Python SDK and Responses API when the key is present. Without a key, it runs a deterministic demo mode so the UI can still be demonstrated.

## Important
Never commit `.env` or expose an API key in GitHub. `.env` is included in `.gitignore`.

## Suggested demo
Try:
> I want to start a small fast-food shop near my college with a limited budget.

Then show the assumptions, blind spots, risk map, alternatives and **Break My Decision** section.
