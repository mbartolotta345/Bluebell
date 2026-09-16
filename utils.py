from functools import wraps

from flask import jsonify, session

from datetime import date, datetime, timedelta


def utcnow_naive():
    return datetime.utcnow()


def current_user_id():
    return session.get("user_id")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user_id():
            return jsonify({"errors": ["You must be logged in."]}), 401
        return view(*args, **kwargs)

    return wrapped


def next_due_date(plant):
    return plant.last_watered_at.date() + timedelta(days=plant.watering_frequency_days)


def days_overdue(plant, today=None):
    today = today or date.today()
    return (today - next_due_date(plant)).days


def is_thirsty(plant, today=None):
    return days_overdue(plant, today) >= 0


def catch_up_watering(plant, today=None):
    """There's no manual 'mark watered' action - the app assumes each
    plant gets watered on the day it's due. Once a due date is fully in
    the past, roll last_watered_at forward that many cycles so the plant
    settles back to "due today" (or later) instead of piling up as
    overdue. Returns True if last_watered_at changed (caller should
    commit)."""
    today = today or date.today()
    changed = False
    while next_due_date(plant) < today:
        plant.last_watered_at = plant.last_watered_at + timedelta(days=plant.watering_frequency_days)
        changed = True
    return changed


def plant_with_schedule(plant):
    catch_up_watering(plant)
    data = plant.to_dict()
    due = next_due_date(plant)
    data["next_due_date"] = due.isoformat()
    data["days_overdue"] = days_overdue(plant)
    data["is_thirsty"] = is_thirsty(plant)
    return data
