<p align="center">
  <img src="static/bluebell-logo-smaller.png" alt="Bluebell logo" width="300">
</p>

# Keep Your Plants Alive

A plant watering/care tracker. Users add, edit, and remove plants with no
account at all; signing in with Google is only needed if you want SMS/email
reminders. Flask + SQLite backend, plain HTML/CSS/JS frontend.

## Features

- Add plants with a name, species, watering frequency, sunlight needs, and
  notes; edit or remove them inline. There's no manual "mark watered"
  button - the schedule assumes each plant gets watered on the day it's
  due and rolls forward automatically, so it always shows the current
  due date rather than piling up as overdue.
- The report view flags any plant that's due for watering today and shows
  its exact next-due date.
- Optional daily or when needed reminder digests by SMS and/or email, opt-in per signed-in
  Google account, for plants that are due.
- Bluebell-branded landing page with a video hero above the tracker.

## Overview

![App overview](docs/overview.gif)
