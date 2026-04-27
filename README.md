# NYC Street Lights — 311 Complaint Dashboard

AI-assisted 311 street-lamp complaint assessment & work-order generator for all 5 NYC boroughs. Built on 10,000 real closed/open/pending NYC 311 records and 1,875 licensed NYC electrical contractors.

## Project layout

```
NYC Street Lights/
├─ public/
│  └─ index.html                  # generated dashboard (do not edit directly)
├─ api/
│  └─ generate-work-order.py      # Vercel serverless function (calls Claude)
├─ data/
│  ├─ Staten_Island.csv           # 2,000 rows, Nov 2018 – Dec 2019
│  ├─ Manhattan.csv
│  ├─ Bronx.csv
│  ├─ Brooklyn.csv
│  ├─ Queens.csv
│  └─ vendors_final.csv           # 1,875 NYC electricians
├─ build.py                       # generates public/index.html from data/
├─ vercel.json
├─ requirements.txt
└─ README.md
```

## Local development

```bash
# 1. Rebuild the dashboard whenever you change build.py or data/
python build.py

# 2. Serve the public/ folder so Google Maps API referrer checks pass
cd public
python -m http.server 8000
# then open http://127.0.0.1:8000/index.html
```

The **Create Work Order with AI** button requires the `/api/generate-work-order` endpoint to be reachable. For local testing you have two options:

- **Vercel CLI** (recommended): `npm i -g vercel`, then `vercel dev` from the project root. This serves both the static site and the Python function together.
- **Skip locally**: only test the AI button after deploying to Vercel.

## Deploy to Vercel

1. Sign in at [vercel.com](https://vercel.com) and create a new project pointing at this folder (or push to GitHub and import the repo).
2. During setup Vercel detects this as a static site with a Python function — no framework preset needed. Leave the build command empty and set **Output Directory** to `public`.
3. Go to **Project Settings → Environment Variables** and add:
   - `ANTHROPIC_API_KEY` → your paid-workspace Claude key (required)
   - `ALLOWED_ORIGIN`    → your Vercel domain, e.g. `https://nyc-street-lights.vercel.app` (optional; defaults to `*` for dev)
   - `ANTHROPIC_MODEL`   → e.g. `claude-sonnet-4-5` (optional; default is `claude-sonnet-4-5`)
4. Redeploy. The dashboard lives at `/` and the function at `/api/generate-work-order`.

### Anthropic cost controls
Before going public, open the [Anthropic console](https://console.anthropic.com/) → **Settings → Billing** → **Spend limits** and set a monthly cap. A single work-order request is ~2,500 input tokens + ~600 output tokens (~\$0.015 on Sonnet 4.5 at time of writing).

The serverless function enforces a **per-IP limit of 10 requests/hour** in memory. For stricter enforcement, swap the in-memory `_rate_bucket` in `api/generate-work-order.py` for [Vercel KV](https://vercel.com/docs/storage/vercel-kv) or Upstash Redis.

## Data refresh

Replace any CSV in `data/` (same column names) and rerun `python build.py`. Supported columns from Snowflake `LIGHT_COMPLAINTS` + dimension joins:

```
UNIQUE_KEY, CREATED_DATE, PROBLEM_DETAIL, INCIDENT_ADDRESS,
STREET_NAME, INCIDENT_ZIP, STATUS, DAYS_TO_CLOSE, LATITUDE, LONGITUDE
```

Vendor CSV columns:

```
license_number, business_name, address, city, state, zip, borough, email, phone, status, lat, long
```

## Features

- **NYC-wide coverage** — borough selector + dynamic ZIP filter
- **Google Places autocomplete** bounded to NYC (auto-fills borough + ZIP)
- **Cosine-similarity engine** finds the 5 most similar past complaints
- **Distance-ranked vendor assignment** (same ZIP → same borough → nearest by haversine)
- **Full-viewport map view** after submission with color-coded markers + driving route
- **AI work order generator** — calls Claude with the 5 similar complaints as few-shot examples
- **Copy / Download** work-order JSON

## Security notes

- The Google Maps API key in `build.py` is public (browser-exposed). Lock it down in Google Cloud Console with HTTP-referrer restrictions pointing at your Vercel domain.
- The Anthropic API key is **server-side only** — it lives in a Vercel environment variable and is never sent to the browser.
- The serverless function caps request size (32 KB), limits few-shot examples (5), and rate-limits per IP (10/hr).
