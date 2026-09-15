Build a full-stack web app called "Keep Your Plants Alive" — a plant watering/care tracker with AI-assisted care suggestions and optional email/SMS reminders. Build this from scratch in the current directory. Work incrementally, running/testing each piece as you go rather than writing everything blind, and tell me what you're doing at each major step.

## Tech Stack
- Backend: Python 3 + Flask (REST API)
- Database: SQLite for local development (use SQLAlchemy so migrating to Postgres later is easy)
- Frontend: Plain HTML/CSS/JS, single page, served by Flask (no build tooling, no frontend framework)
- AI lookup: Claude API (Anthropic Python SDK) with the web search tool enabled, for optional care-suggestion lookups
- Scheduling: A simple local scheduled job (e.g. APScheduler or a standalone script intended to be run via cron) for the daily reminder check — do not build AWS infrastructure (Lambda/EventBridge/SNS/SES) at this stage; use a local SMTP-based email send (or a stubbed email function) and a stubbed/print-based SMS send for now, structured so they can be swapped for AWS SES/SNS later
- Config: Use a `.env` file (with a `.env.example` committed) for the Anthropic API key, email credentials, and any other secrets. Never hardcode secrets.

## Database Schema
Create these tables via SQLAlchemy models:

**plants**
- id (primary key)
- name (text, required)
- species (text, required)
- watering_frequency_days (integer, required)
- sunlight_needs (text, required)
- used_ai_suggestion (boolean, default false)
- ai_explanation (text, nullable)
- ai_sources (JSON/text, nullable — store as a list of URLs)
- last_watered_at (datetime, required)
- created_at (datetime, default now)
- notes (text, nullable)
- active (boolean, default true — used for soft-delete)

**contact_settings**
- id (primary key, single row for this app)
- phone_number (text, nullable)
- email (text, nullable)
- updated_at (datetime)

**watering_log**
- id (primary key)
- plant_id (foreign key -> plants.id)
- watered_at (datetime)

**notifications_log**
- id (primary key)
- plant_id (foreign key -> plants.id)
- sent_at (datetime)
- channel (text — "sms" or "email")
- digest_id (text, nullable — groups plants sent together in the same daily digest)

## REST API Endpoints
- `GET /plants` — list all active plants (this is also the data source for the report view)
- `GET /plants/:id` — get one plant's details
- `POST /plants` — create a plant
- `PUT /plants/:id` — update a plant's fields (used both for direct edits and for report-view edits)
- `DELETE /plants/:id` — soft-delete a plant (set active = false)
- `POST /plants/:id/water` — mark a plant watered now: update last_watered_at to now, insert a row into watering_log
- `GET /plants/thirsty` — list plants currently overdue for watering (last_watered_at + watering_frequency_days <= today), including days_overdue
- `GET /plants/:id/history` — watering history for one plant, from watering_log
- `POST /plants/ai-suggest` — body: `{ "species": "..." }`. Calls the Claude API with web search enabled, and returns:
  ```json
  {
    "suggested_frequency_days": 6,
    "suggested_sunlight": "Bright, indirect light",
    "explanation": "1-2 sentence explanation covering both watering and sunlight",
    "sources": ["https://...", "https://..."]
  }
  ```
  This endpoint does NOT save anything — it just returns a suggestion for the frontend to display and pre-fill. The Anthropic API key must only ever be used server-side, never sent to the frontend.
- `GET /contact` — get current contact_settings row
- `PUT /contact` — update phone_number / email (either or both can be null/empty — contact info is entirely optional)

## Thirsty / Reminder Logic
A plant is "thirsty" when `last_watered_at + watering_frequency_days <= today`.

Build a scheduled daily job (runnable both via APScheduler inside the app and as a standalone script for cron) that:
1. Finds all thirsty plants.
2. Filters out plants already alerted for their current overdue period (check notifications_log so we don't re-alert every single day for the same overdue stretch — re-alert only if it's been a few days since the last alert for that plant).
3. Groups ALL thirsty plants found in one run into a single digest per channel (not one message per plant).
4. If contact_settings has a phone_number, "send" (print/log for now, structured so it can swap to AWS SNS later) a SHORT SMS-style digest — just plant names/count, e.g. "3 plants need water today: Fernando the Fern, Aloe, Pothos."
5. If contact_settings has an email, send (via SMTP or a stubbed function, structured so it can swap to AWS SES later) a MORE DETAILED email digest — per-plant breakdown with last watered date, exact next-due date, and days overdue.
6. If contact_settings has neither phone nor email set, skip sending entirely — this must not error, since reminders are fully optional.
7. Log every send to notifications_log with a shared digest_id.

## Frontend (single page, HTML/CSS/JS)
One page containing:

1. **Header section**
   - Headline: "Keep your plants alive"
   - Subheading: "Individual care schedule and reminders for your plants, input your plants now!"
   - Background: an animated light-to-dark green gradient that moves slowly like a wave (CSS keyframe animation on background-position or a gradient mesh — should feel calm and organic, not distracting; content must stay clearly readable on top of it).

2. **Add-a-plant form**
   - Fields: Name, Species, Last Watered (date picker), and a checkbox "Use AI to suggest care schedule."
   - If the checkbox is checked: after Species is entered, call `POST /plants/ai-suggest` and auto-fill Watering Frequency (days) and Sunlight Needs fields with the response, displaying the brief AI explanation and clickable source links right below the fields. Both auto-filled fields remain editable before saving.
   - If the checkbox is unchecked: show empty Watering Frequency (days) and Sunlight Needs fields for manual entry.
   - A Notes field (optional).
   - Save button calls `POST /plants`.

3. **Report / plant list (same page, not a separate route)**
   - A card or table per plant showing: name, species, watering frequency, sunlight needs, last watered date, and next watering due date shown as an EXACT date (e.g. "Next watering: Sept 18, 2026") — not relative phrasing like "in 2 days."
   - Each plant has Edit and Remove controls inline. Edit lets the user change any field directly in the report and saves via `PUT /plants/:id`. Remove calls `DELETE /plants/:id`.
   - A "Mark watered" button per plant that calls `POST /plants/:id/water` and refreshes the displayed dates.
   - Plants that are currently thirsty should be visually flagged (e.g. a droplet icon or a warning color on the card).
   - This report must be fully usable without ever touching the contact info section below — no contact info required to add, view, or edit plants.

4. **Contact info section (optional, clearly separate)**
   - Phone number field and Email field, either or both can be filled in.
   - Clear framing that this step is optional and only needed if the user wants reminders.
   - Save button calls `PUT /contact`.

Keep the visual style minimal, calm, and plant/nature themed — generous whitespace, soft rounded corners on cards, mobile-friendly layout.

## Project Structure
Set up something like:
```
/app.py or /run.py          (Flask entrypoint)
/models.py                  (SQLAlchemy models)
/routes/ or blueprints       (organize endpoints sensibly)
/services/ai_lookup.py      (Claude API call logic)
/services/notifications.py (digest-building + send logic, stubbed SNS/SES-ready)
/scheduler.py                (daily job, runnable standalone or via APScheduler)
/static/                     (CSS/JS)
/templates/index.html        (the single page)
/.env.example
/requirements.txt
/README.md
```

## Other requirements
- Include a `requirements.txt` with all dependencies pinned to reasonable versions.
- Include a `README.md` explaining: how to install dependencies, how to set up the `.env` file (including where to get an Anthropic API key), how to run the app locally, and how to run the scheduled reminder job manually for testing.
- Seed the SQLite database automatically (create tables) on first run if they don't exist.
- Write basic input validation on the API (e.g. required fields present, watering_frequency_days is a positive integer).
- Do not build any AWS deployment infrastructure yet (no Lambda/EventBridge/SAM/Serverless configs) — this phase is local-only. Structure the notification-sending code so swapping in AWS SES/SNS later is a small, contained change.
- After building, run the app locally and verify the endpoints work (e.g. via curl or a simple test script) before telling me it's done.

Ask me if anything above is ambiguous before making a major architectural assumption, but otherwise proceed and build the whole thing.
