# Outbound-call demo proxy

Server-side endpoint that lets `outboundcalldemo.html` place a **real** Vapi
outbound call without ever exposing the Vapi key in public site files.

It is **not** part of the GitHub Pages site (Pages can't run servers). Deploy it
separately, then point the demo at it.

## Flow
```
browser demo  --POST {name,phone}-->  this proxy  --Vapi API-->  outbound call
              (no key in browser)     (holds key)
```

## One-click deploy configs (pick one)
This folder ships ready-made configs so you don't write any:
- **Render** — `render.yaml` blueprint. Render → New → Blueprint → this repo;
  it provisions the service and prompts for the 3 secret env vars.
- **Railway** — `railway.json` (Nixpacks, healthcheck). New Project → Deploy from
  repo, set root dir to `call-proxy/`, add the env vars.
- **Fly / Cloud Run / any container** — `Dockerfile` (+ `.dockerignore`).
- **Heroku-style** — `Procfile`.

All of them just need the 3 Vapi env vars set in the host dashboard (see below).

## Deploy steps
1. (local check) `cd call-proxy && npm install && npm start`
2. Set env vars on the host from `.env.example` — the three Vapi values from the
   Vapi dashboard (private key, assistant id, phone-number id). **Never commit `.env`.**
3. Deploy. Confirm `GET /healthz` returns `{ "ok": true }`.
4. Copy the public URL of `POST /api/demo-call` (e.g.
   `https://your-app.up.railway.app/api/demo-call`).
5. In `outboundcalldemo.html`, set:
   ```js
   const CALL_PROXY_URL = 'https://your-app.up.railway.app/api/demo-call';
   ```
   Commit + push. The sim banner auto-hides and the demo now places real calls.

## Guardrails (keep these on)
This endpoint dials real numbers and costs money per call, and it's public.
- **ALLOWED_ORIGIN** — only the live site origin is accepted (CORS).
- **Per-IP rate limit** — `RATE_LIMIT_MAX` calls per `RATE_LIMIT_WINDOW_MS`.
- **E.164 validation** — malformed numbers rejected before hitting Vapi.
- **Consent** — the demo's consent checkbox is enforced client-side; for real
  campaigns also scrub against DNC lists (TCPA / AU Spam Act).

The in-memory rate limiter resets on restart and is per-instance; use Redis or a
provider-level limit if you run more than one instance.
