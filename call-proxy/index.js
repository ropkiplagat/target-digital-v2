// Target Digital — outbound-call demo proxy.
//
// The browser demo (outboundcalldemo.html) POSTs {name, phone, source} here.
// This server holds the Vapi PRIVATE key (never shipped to the browser) and
// triggers the outbound call server-side.
//
// ⚠️ This endpoint dials real phone numbers and costs money per call. It is
// PUBLIC by nature (the site is public), so it is an abuse target (toll fraud,
// harassment). The guardrails below are the minimum — keep them on:
//   • ALLOWED_ORIGIN   — only accept requests from the live site
//   • per-IP rate limit — cap calls per window
//   • E.164 validation  — reject malformed numbers
//   • consent is enforced client-side; do NOT remove the checkbox there
//
// Deploy on any Node host (Railway / Render / Fly / a serverless function).
// Set the env vars from .env.example, then put this service's URL into
// CALL_PROXY_URL in outboundcalldemo.html.

import express from "express";

const {
  VAPI_PRIVATE_KEY,
  VAPI_ASSISTANT_ID,
  VAPI_PHONE_NUMBER_ID,
  ALLOWED_ORIGIN = "https://targetdigital.com.au",
  RATE_LIMIT_MAX = "5",
  RATE_LIMIT_WINDOW_MS = "3600000", // 1 hour
  MAX_CALLS_PER_DAY = "25", // global backstop so IP rotation can't run up the bill
  ALLOWED_COUNTRY_PREFIXES = "+61", // comma list; toll-fraud dials expensive foreign numbers
  PORT = "3000",
} = process.env;

for (const [k, v] of Object.entries({
  VAPI_PRIVATE_KEY,
  VAPI_ASSISTANT_ID,
  VAPI_PHONE_NUMBER_ID,
})) {
  if (!v) {
    console.error(`Missing required env var: ${k}. See .env.example.`);
    process.exit(1);
  }
}

const app = express();
// Trust exactly one proxy hop (the host's load balancer) so req.ip is the real
// client IP. Without this, the rate limiter keyed off a client-controlled
// X-Forwarded-For header — trivially spoofable to bypass the per-IP cap.
app.set("trust proxy", 1);
app.use(express.json({ limit: "8kb" }));

// --- CORS: only the live site may call this proxy ---
app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (origin === ALLOWED_ORIGIN) {
    res.setHeader("Access-Control-Allow-Origin", ALLOWED_ORIGIN);
    res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  }
  if (req.method === "OPTIONS") return res.sendStatus(204);
  next();
});

// --- Tiny in-memory per-IP rate limiter (swap for Redis if you scale out) ---
const hits = new Map(); // ip -> [timestamps]
const MAX = parseInt(RATE_LIMIT_MAX, 10);
const WINDOW = parseInt(RATE_LIMIT_WINDOW_MS, 10);
function rateLimited(ip, now) {
  const recent = (hits.get(ip) || []).filter((t) => now - t < WINDOW);
  if (recent.length >= MAX) {
    hits.set(ip, recent);
    return true;
  }
  recent.push(now);
  hits.set(ip, recent);
  return false;
}

// E.164: +, country digit 1-9, up to 14 more digits.
const E164 = /^\+[1-9]\d{6,14}$/;

// Country allowlist — only numbers starting with one of these prefixes are
// dialed. Blocks the classic toll-fraud vector (premium/expensive foreign
// numbers). Configure via ALLOWED_COUNTRY_PREFIXES (comma-separated, e.g. "+61,+64").
const COUNTRY_PREFIXES = ALLOWED_COUNTRY_PREFIXES.split(",")
  .map((p) => p.trim())
  .filter(Boolean);

// Global daily cap — a hard ceiling on real calls per UTC day, independent of
// IP. The per-IP limit doesn't stop an attacker rotating IPs; this does.
const DAILY_MAX = parseInt(MAX_CALLS_PER_DAY, 10);
let dailyCount = 0;
let dailyKey = "";
function overDailyCap(now) {
  const key = new Date(now).toISOString().slice(0, 10); // YYYY-MM-DD (UTC)
  if (key !== dailyKey) {
    dailyKey = key;
    dailyCount = 0;
  }
  if (dailyCount >= DAILY_MAX) return true;
  dailyCount += 1;
  return false;
}

app.post("/api/demo-call", async (req, res) => {
  const ip = req.ip || "unknown";
  const now = Date.now();

  if (rateLimited(ip, now)) {
    return res.status(429).json({ error: "Too many demo calls. Try later." });
  }

  const { name, phone } = req.body || {};
  const cleanPhone = typeof phone === "string" ? phone.replace(/[\s()-]/g, "") : "";
  if (!cleanPhone || !E164.test(cleanPhone)) {
    return res
      .status(400)
      .json({ error: "Phone must be E.164 format, e.g. +61412345678." });
  }
  if (!COUNTRY_PREFIXES.some((p) => cleanPhone.startsWith(p))) {
    return res
      .status(400)
      .json({ error: "That country isn't supported for the demo." });
  }
  // Reserve a daily slot only now that we know the request is valid + dialable,
  // so rejected requests don't burn the global cap.
  if (overDailyCap(now)) {
    return res
      .status(429)
      .json({ error: "Daily demo-call limit reached. Try again tomorrow." });
  }
  const cleanName =
    typeof name === "string" ? name.trim().slice(0, 80) : "Demo prospect";

  try {
    const r = await fetch("https://api.vapi.ai/call", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${VAPI_PRIVATE_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        assistantId: VAPI_ASSISTANT_ID,
        phoneNumberId: VAPI_PHONE_NUMBER_ID,
        customer: { number: cleanPhone, name: cleanName },
      }),
    });

    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      console.error("[demo-call] Vapi error", r.status, data);
      return res.status(502).json({ error: "Call provider rejected the request." });
    }
    console.log(`[demo-call] placed call id=${data.id} to ${cleanPhone} (ip ${ip})`);
    return res.json({ ok: true, id: data.id });
  } catch (err) {
    console.error("[demo-call] proxy failure:", err);
    return res.status(500).json({ error: "Could not place the call." });
  }
});

app.get("/healthz", (_req, res) => res.json({ ok: true }));

app.listen(parseInt(PORT, 10), () => {
  console.log(`call-proxy listening on :${PORT} (origin ${ALLOWED_ORIGIN})`);
});
