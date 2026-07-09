# AI Gateway Frontend

This is a simple React frontend for the AI Gateway backend. It is intentionally lightweight and designed to help backend developers quickly test the existing API without building a full product UI.

## What it does

- registers and logs in a user
- creates an API key using the backend `/key/` endpoint
- sends a chat prompt to `/v1/chat/completions`
- displays the streamed response in a simple conversation view
- includes a basic dark palette and subtle animations for a modern look

## Why this is useful for a backend dev

If you are working on the backend, this frontend helps you validate the complete flow:

- authentication via `/auth/register` and `/auth/login`
- API key creation and usage
- gateway routing to Gemini or Groq models
- request and response handling from the client

It keeps the UI simple so you can focus on backend behavior instead of frontend complexity.

## Setup

From the `frontend` folder:

```bash
npm install
npm run dev
```

By default, the frontend expects the backend to run at `http://localhost:8000`.

If your backend runs on a different address, create a `.env` file in `frontend` with:

```env
VITE_BACKEND_URL=http://localhost:8000
```

Then restart the dev server.

## Deployment

This frontend is a static React app that can be built and served by any static hosting provider.

From the `frontend` folder:

```bash
npm run build
```

The production build files will be created in `dist/`.

You can deploy `dist/` to providers like Vercel, Netlify, GitHub Pages, or any web server.

If your backend is deployed separately, make sure the deployed frontend uses the correct `VITE_BACKEND_URL`.

## Developer notes

- This app is intentionally simple and uses only React + Vite.
- It does not store any credentials securely across refreshes.
- The key flow is: register/login → create API key → call gateway endpoint.
- The app uses the backend's existing `/auth`, `/key`, and `/v1/chat/completions` routes.
- Keep backend CORS enabled if you access this frontend from a different host.

## How to use it

1. Open the app in your browser.
2. Register a new user using email and password.
3. Login with the same credentials.
4. Create a new API key.
5. Switch to the Chat tab and paste the generated API key.
6. Send a prompt and review the assistant response.

## Notes

- The app uses a minimal React setup with Vite.
- It does not persist authentication across refreshes.
- It is meant as a prototype/test client, not a production-ready app.
