<p align="center">
  <img src="static/bluebell-logo-smaller.png" alt="Bluebell logo" width="300">
</p>

# Keep Your Plants Alive

A plant watering/care tracker. Users add, edit, water, and remove
plants with no account at all; signing in with Google is only needed if you
want SMS/email reminders. Flask + SQLite backend, plain HTML/CSS/JS frontend.

## Features

- Add plants with a name, species, watering frequency, sunlight needs, and
  notes.
- Use autofill from houseplant species database to input your plant's needs with sources attatched.
- The report view flags any plant that's currently overdue for watering and
  shows its exact next-due date.
- Optional daily or when needed reminder digests by SMS and/or email, opt-in per signed-in
  Google account, for plants that are overdue.
- Bluebell-branded landing page with a video hero above the tracker.

## Demo

![App overview](docs/overview.gif)

## Future Iterations
- Add Api Google Custom Search to find best plant websites to reccommend plant needs and source attatchment instead of database.
- Fertilizer tracking
- Photo Tracking
- Custom schedules and linking to Google Calendar
