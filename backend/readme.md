# AI Gateway Backend

AI Gateway is a FastAPI-based backend that exposes a unified API for interacting with multiple large language model providers, including Gemini and Groq. It is designed to be simple for clients to use while handling authentication, API key management, request routing, caching, rate limiting, and audit logging behind the scenes.

## Overview

This project acts as a gateway between your application and upstream AI providers. Instead of integrating directly with provider SDKs from the client side, you can send requests to a single backend endpoint and let the gateway:

- authenticate users and API keys,
- choose the appropriate provider based on the requested model,
- stream responses back to the client,
- cache repeat requests in Redis,
- track usage and cost-related metadata in PostgreSQL.

## Main Features

- User registration and login with JWT-based authentication
- API key creation, listing, and revocation for client access
- Unified chat endpoint at `/v1/chat/completions`
- Provider routing for Gemini and Groq models
- Streaming responses using Server-Sent Events
- Redis-backed response caching
- Per-API-key rate limiting
- Audit logging for provider usage and status

## Tech Stack

- FastAPI for the API layer
- Async SQLAlchemy for database access
- PostgreSQL for users, API keys, and audit logs
- Redis for caching and rate limiting
- Alembic for database migrations
- Pydantic and Pydantic Settings for schema validation and configuration
- JWT for authentication
- Google GenAI SDK and Groq SDK for model access

## Project Structure

- `app/main.py` – FastAPI application entrypoint and middleware
- `app/routes/` – authentication, API key, and gateway endpoints
- `app/services/` – business logic for auth, API keys, Redis, and caching
- `app/dependencies/` – authentication and request validation helpers
- `app/provider/` – provider-specific integrations for Gemini and Groq
- `app/models/` – SQLAlchemy models for users, API keys, and audit logs
- `app/schemas/` – request and response models
- `app/alembic/` – database migration files

## Prerequisites

Before running the backend, make sure you have:

- Python 3.10 or newer
- PostgreSQL running and reachable
- Redis running locally or remotely
- API keys for Gemini and/or Groq

## Environment Configuration

Create a `.env` file in the backend project root with the following variables:

```env
Hello_URL=http://localhost:8000
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/ai_gateway
ACCESS_TOKEN_EXPIRY_MINUTES=60
SECRET_KEY=your-secret-key
ALGORITHM=HS256
GEMINI_API_KEY=your-gemini-key
REDIS_URL=redis://localhost:6379/0
GROQ_API_KEY=your-groq-key
```

## Local Setup

1. Open the backend folder:

```bash
cd backend
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up the database with Alembic:

```bash
pip install alembic
alembic upgrade head
```

If you change the SQLAlchemy models and need to create a new migration later, run:

```bash
alembic revision --autogenerate -m "describe_your_change"
alembic upgrade head
```

To roll back the most recent migration:

```bash
alembic downgrade -1
```

5. Start the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will then be available at `http://localhost:8000`.

## API Endpoints

### Health Check

- `GET /` – checks whether the API and Redis are healthy

### Authentication

- `POST /auth/register` – create a new user account
- `POST /auth/login` – login and receive a JWT access token
- `GET /auth/me` – fetch the current authenticated user

### API Key Management

- `POST /key/` – create a new API key for the authenticated user
- `GET /key/` – list API keys for the authenticated user
- `DELETE /key/{key_id}` – revoke an API key

### AI Gateway

- `POST /v1/chat/completions` – send a chat request to the gateway

## Example Usage

### 1. Register a user

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"strongpassword"}'
```

### 2. Login and get a token

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=strongpassword"
```

### 3. Create an API key

```bash
curl -X POST "http://localhost:8000/key/" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"my-client-app"}'
```

### 4. Send a chat request

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-2.5-flash",
    "temperature": 0.7,
    "messages": [{"role": "user", "content": "Is Python a high-level or low-level language?"}]
  }'
```

If you are testing through Swagger UI, use this request body:

```json
{
  "model": "gemini-2.5-flash",
  "temperature": 0.7,
  "messages": [
    {
      "role": "user",
      "content": "Is Python a high-level or low-level language?"
    }
  ]
}
```

## Notes and Behavior

- Requests to `/v1/chat/completions` are protected by API key authentication.
- The gateway currently applies a basic rate limit of 5 requests per minute per active API key.
- Responses are streamed back as Server-Sent Events.
- Redis is used to cache responses for repeated prompts.
- If the primary provider fails during streaming, the gateway attempts a fallback path through Groq.

## Next Improvements

Potential future enhancements include:

- support for more providers,
- better token usage reporting,
- request/response logging dashboards,
- admin tools for managing users and keys,
- more robust observability and metrics.
