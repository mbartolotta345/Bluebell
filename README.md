# Keep Your Plants Alive

A plant watering/care tracker with care-suggestion lookups and optional
email/SMS reminders. Flask + SQLite backend, plain HTML/CSS/JS frontend.
Adding, editing, and watering plants works for anyone with no account
needed; signing in with Google is only required to set up reminders, since
that's the one feature that needs to know who to contact.

## Install dependencies

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

## Set up the `.env` file

Copy `.env.example` to `.env` and fill in the values you need:

```bash
cp .env.example .env
```

- **`GOOGLE_OAUTH_CLIENT_ID`** - required for "Sign in with Google", which
  gates only the Reminders section (the plant tracker itself needs no
  login). Set it up:
  1. Go to https://console.cloud.google.com/apis/credentials
  2. Click **Create Credentials > OAuth client ID**, application type
     **Web application**.
  3. Under **Authorized JavaScript origins**, add both
     `http://127.0.0.1:5000` and `http://localhost:5000` for local dev.
  4. Copy the generated **Client ID** into `GOOGLE_OAUTH_CLIENT_ID`.

- **`SECRET_KEY`** - required to keep users logged in across server
  restarts. Generate one with:
  `python -c "import secrets; print(secrets.token_hex(32))"`.
  If left blank, a random key is generated at every startup, which logs
  everyone out whenever the server restarts.

- **`GOOGLE_API_KEY` / `GOOGLE_CSE_ID`** - powers the "care schedule
  suggestion" lookup via Google Custom Search, which extracts a watering
  frequency / sunlight phrase from search results with simple pattern
  matching (no LLM involved, so treat the result as a starting point to
  double check, not a verified fact). Free for up to 100 searches/day.
  1. Go to https://console.cloud.google.com/apis/library/customsearch.googleapis.com
     and enable the **Custom Search API** on a Google Cloud project (create
     one first if you don't have one - no billing required for the free tier,
     though some accounts do need a billing account linked before any API
     will actually activate).
  2. Go to https://console.cloud.google.com/apis/credentials, click
     **Create Credentials > API Key**, and copy it into `GOOGLE_API_KEY`.
     Restrict it (API restrictions) to just the Custom Search API.
  3. Go to https://programmablesearchengine.google.com/, create a new search
     engine (set it to search the entire web), and copy its **Search engine
     ID** into `GOOGLE_CSE_ID`.

  Without these, the lookup endpoint returns an error, but the rest of the
  app (adding/editing/watering plants manually) works fine. Note: this
  feature's frontend UI is currently disabled pending billing setup - see
  the comment in `templates/index.html` for how to re-enable it.

- **`SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM`** -
  optional. If `SMTP_HOST` is left blank, reminder emails are printed to the
  console instead of actually sent - useful for local testing.
- **`REMINDER_HOUR` / `REMINDER_MINUTE`** - what time of day the in-app
  scheduler sends reminders (24h, server local time).
- **`REALERT_INTERVAL_DAYS`** - how many days to wait before re-alerting on a
  plant that's still overdue (so you don't get the same reminder every day).
- **`ENABLE_SCHEDULER`** - set to `true` to run the daily reminder check
  automatically inside the Flask app process (via APScheduler). Leave `false`
  if you'd rather trigger it yourself via cron (see below).

## Run the app locally

```bash
python app.py
```

The database (`plants.db`) is created automatically on first run. Open
http://127.0.0.1:5000 in your browser - you can add, edit, and water plants
right away with no account. Sign in with Google (in the Reminders section)
only if you want SMS/email alerts when your plants are thirsty.

## Run the scheduled reminder job manually

The daily reminder check can be run on demand, independent of the Flask
server - handy for testing or for wiring up to an external cron job:

```bash
python scheduler.py
```

Plants are shared/global (no login needed to manage them), but reminders
are opt-in per signed-in user. This job loops over every user who has
signed in, checks the shared plant list for anything overdue, skips plants
that user was already alerted about recently, and sends them a grouped
digest by SMS and/or email (or prints it to the console if no contact info
/ SMTP is configured for that user). To run it automatically every day via
cron:

```cron
0 8 * * * cd /path/to/project && venv/bin/python scheduler.py
```

## Project structure

```
app.py                  Flask entrypoint
models.py               SQLAlchemy models (users, plants, contact settings, logs)
routes/                 API endpoints (auth, plants - public, contact - login required)
services/ai_lookup.py   Google Custom Search call + heuristic extraction for care suggestions
services/notifications.py  Digest-building + send logic (SMTP/print-based; swap-ready for AWS SES/SNS)
scheduler.py            Daily reminder job (standalone or APScheduler), loops per user
static/                 CSS/JS/images/video
templates/index.html    The single-page frontend
```

## Accounts and access control

Plants are shared/global - anyone can view, add, edit, water, or remove any
plant with no account at all (`/plants...` endpoints are fully public).
Reminder contact settings are the one thing tied to an account
(`models.User`, identified by a verified Google ID token - no password
system): the `/contact` endpoints require an active session, and each
signed-in user manages their own phone/email for alerts about the shared
plant list independently of everyone else's.

## Notes

- Notification sending (`services/notifications.py`) is deliberately kept
  provider-agnostic: `send_sms` / `send_email` are the only two functions
  that would need to change to swap in AWS SNS/SES later.
- The Google API key (Custom Search) and OAuth client secret verification
  are only ever used server-side - neither is exposed to the frontend
  (the OAuth *client ID* is not secret and is safe to embed in the page).
