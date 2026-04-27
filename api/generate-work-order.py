"""
Vercel serverless function: POST /api/generate-work-order
---------------------------------------------------------
Proxies a work-order generation request to Anthropic's Claude API.

Environment variables required in Vercel dashboard:
  ANTHROPIC_API_KEY   (your paid workspace key)

Optional:
  ALLOWED_ORIGIN      (exact origin to allow in CORS; defaults to '*' for dev)
  ANTHROPIC_MODEL     (default: claude-sonnet-4-5)

Safeguards:
  - In-memory per-IP rate limit: 10 requests / hour / IP
  - Hard cap on incoming payload size (~32 KB)
  - Limits prompt details to ~1500 chars and similar-orders to 5
  - max_tokens capped at 1500
  - Validates required fields
  - Strips any markdown code fences Claude emits
"""

import json
import os
import time
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ANTHROPIC_URL     = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL     = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
MAX_TOKENS        = 1500
MAX_BODY_BYTES    = 32 * 1024          # 32 KB
MAX_DETAILS_CHARS = 1500
MAX_EXAMPLES      = 5
RATE_LIMIT_PER_HOUR = 10
ALLOWED_ORIGIN    = os.environ.get("ALLOWED_ORIGIN", "*")

# In-memory rate limit store. Survives for the lifetime of the warm Lambda
# instance (~a few minutes). Good enough to deter casual abuse; for strict
# enforcement use Vercel KV / Upstash Redis.
_rate_bucket = {}   # ip -> list[timestamp]


SYSTEM_PROMPT = """You are an NYC Department of Transportation (DOT) work order generator for streetlight repairs.

You will be shown a new OPEN complaint plus up to 5 SIMILAR RESOLVED past complaints as few-shot examples. The assigned vendor (a licensed NYC electrical contractor) is also provided.

Use the past examples to estimate typical resolution time and material needs, then generate a structured work order JSON for the new complaint.

Work order fields to include (all required unless noted):
- work_order_id         : format "WO-YYYY-NNNNN" using the current year and a 5-digit number from the complaint_id last 5 digits
- complaint_id          : copy from input
- complaint_type        : copy from input (the specific PROBLEM_DETAIL if given, else the category)
- address               : copy from input
- borough               : copy from input
- reported_date         : copy from input
- priority              : "High" if safety hazard (hanging/missing fixture, exposed wiring, knocked-down pole);
                          "Medium" if damaged/broken component or multiple lights out;
                          "Low" if cycling, timing, or dim issue only.
                          IMPORTANT: if the input includes a `priority` field, keep it unless clearly inconsistent with the complaint_type.
- estimated_days_to_complete : integer 1-14, based on patterns in the similar past complaints' days_to_close
- materials_needed      : concise, comma-separated specifics (e.g. "Photocell unit, 150W HPS bulb, weatherproof gasket") or "None - adjustment only"
- instructions          : 2-4 sentences, actionable dispatch steps for the vendor. Reference the address.
- safety_notes          : always include PPE requirement; note traffic control / MPT if work is street-level or on a major road; note lockout/tagout if circuit work.
- assigned_vendor       : copy the vendor name from input if provided
- status                : always "Open"

Return ONLY valid minified JSON. No markdown fences, no preamble, no trailing text."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now(): return int(time.time())


def _rate_limit_check(ip: str) -> bool:
    """Return True if the IP is within the hourly quota, else False."""
    cutoff = _now() - 3600
    hits = [t for t in _rate_bucket.get(ip, []) if t > cutoff]
    if len(hits) >= RATE_LIMIT_PER_HOUR:
        _rate_bucket[ip] = hits
        return False
    hits.append(_now())
    _rate_bucket[ip] = hits
    return True


def _validate_payload(payload: dict):
    if not isinstance(payload, dict):
        raise ValueError("Body must be a JSON object.")
    c = payload.get("complaint")
    if not isinstance(c, dict):
        raise ValueError("Missing `complaint` object.")
    for f in ("complaint_id", "complaint_type", "address", "borough", "reported_date"):
        if not c.get(f):
            raise ValueError(f"complaint.{f} is required.")
    details = c.get("details") or ""
    if len(details) > MAX_DETAILS_CHARS:
        c["details"] = details[:MAX_DETAILS_CHARS]
    examples = payload.get("similar_past_orders") or []
    if not isinstance(examples, list):
        raise ValueError("`similar_past_orders` must be an array.")
    payload["similar_past_orders"] = examples[:MAX_EXAMPLES]
    return payload


def _build_user_message(payload: dict) -> str:
    complaint = payload["complaint"]
    examples  = payload["similar_past_orders"]
    vendor    = payload.get("vendor") or {}

    ex_json = json.dumps(examples, indent=2, default=str) if examples else "(none available)"
    vendor_block = ""
    if vendor.get("name"):
        vendor_block = (
            "\nAssigned vendor (licensed NYC electrician):\n"
            f"  name:    {vendor.get('name','')}\n"
            f"  phone:   {vendor.get('phone','')}\n"
            f"  email:   {vendor.get('email','')}\n"
            f"  license: {vendor.get('license','')}\n"
        )
    return (
        "Here are similar resolved NYC streetlight complaints from our database:\n\n"
        f"{ex_json}\n"
        f"{vendor_block}\n"
        "Now generate the work order for this new OPEN complaint:\n\n"
        f"complaint_id:   {complaint.get('complaint_id')}\n"
        f"complaint_type: {complaint.get('complaint_type')}\n"
        f"address:        {complaint.get('address')}\n"
        f"borough:        {complaint.get('borough')}\n"
        f"zip:            {complaint.get('zip','')}\n"
        f"reported_date:  {complaint.get('reported_date')}\n"
        f"priority_hint:  {complaint.get('priority','')}\n"
        f"urgency_score:  {complaint.get('urgency_score','')}\n"
        f"user_details:   {complaint.get('details','(none provided)')}\n\n"
        "Return ONLY the work order JSON object."
    )


def _call_anthropic(api_key: str, user_msg: str, model: str) -> dict:
    body = json.dumps({
        "model":      model,
        "max_tokens": MAX_TOKENS,
        "system":     SYSTEM_PROMPT,
        "messages":   [{"role": "user", "content": user_msg}],
    }).encode("utf-8")

    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
        },
    )

    # Retry on transient Anthropic errors: 429 (rate), 502/503/504 (gateway),
    # 529 (overloaded). Exponential backoff: 1s, 3s, 7s.
    last_err = None
    raw = None
    for attempt, backoff in enumerate([1, 3, 7, 0]):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read().decode("utf-8")
            break
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 502, 503, 504, 529) and backoff:
                time.sleep(backoff)
                continue
            raise
    if raw is None and last_err is not None:
        raise last_err

    data = json.loads(raw)
    text = data.get("content", [{}])[0].get("text", "").strip()

    # Strip markdown fences if Claude ignored instructions
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip("` \n")
    return json.loads(text)


# ---------------------------------------------------------------------------
# Vercel Python handler
# ---------------------------------------------------------------------------
class handler(BaseHTTPRequestHandler):

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")

    def _reply(self, status: int, obj):
        payload = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors()
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_POST(self):
        # Rate limit by IP
        ip = (
            self.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or self.client_address[0]
            or "unknown"
        )
        if not _rate_limit_check(ip):
            return self._reply(429, {"error": "Rate limit exceeded. Try again in an hour."})

        # Size guard
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY_BYTES:
            return self._reply(413, {"error": f"Request body must be 1-{MAX_BODY_BYTES} bytes."})

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as e:
            return self._reply(400, {"error": f"Invalid JSON body: {e}"})

        try:
            payload = _validate_payload(payload)
        except ValueError as e:
            return self._reply(400, {"error": str(e)})

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return self._reply(500, {
                "error": "Server is missing ANTHROPIC_API_KEY. Set it in the Vercel dashboard under Project Settings → Environment Variables."
            })

        user_msg = _build_user_message(payload)
        try:
            work_order = _call_anthropic(api_key, user_msg, DEFAULT_MODEL)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:400]
            if e.code == 529:
                return self._reply(503, {
                    "error": "Claude is temporarily overloaded. Please try again in a moment.",
                    "detail": detail,
                })
            if e.code == 401:
                return self._reply(500, {
                    "error": "Invalid ANTHROPIC_API_KEY on the server.",
                    "detail": detail,
                })
            return self._reply(502, {"error": f"Anthropic API error {e.code}", "detail": detail})
        except urllib.error.URLError as e:
            return self._reply(504, {"error": f"Anthropic API unreachable: {e.reason}"})
        except json.JSONDecodeError:
            return self._reply(502, {"error": "Claude returned a non-JSON response."})
        except Exception as e:
            return self._reply(500, {"error": f"Unexpected error: {type(e).__name__}: {e}"})

        return self._reply(200, work_order)
