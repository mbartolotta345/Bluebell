from datetime import datetime

from flask import Blueprint, jsonify, request

from models import Plant, db
from services.ai_lookup import AiLookupError, get_care_suggestion
from utils import plant_with_schedule

plants_bp = Blueprint("plants", __name__)


def _parse_datetime(value, field_name):
    if isinstance(value, str) and value:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    raise ValueError(f"'{field_name}' must be a valid date/datetime string")


def _validate_plant_payload(data, partial=False):
    errors = []
    required = ["name", "species", "watering_frequency_days", "sunlight_needs", "last_watered_at"]

    for field in required:
        if not partial and (field not in data or data[field] in (None, "")):
            errors.append(f"'{field}' is required")

    if "watering_frequency_days" in data and data["watering_frequency_days"] not in (None, ""):
        try:
            freq = int(data["watering_frequency_days"])
            if freq <= 0:
                errors.append("'watering_frequency_days' must be a positive integer")
        except (ValueError, TypeError):
            errors.append("'watering_frequency_days' must be a positive integer")

    if "name" in data and not partial and not str(data.get("name", "")).strip():
        errors.append("'name' must not be blank")

    if "species" in data and not partial and not str(data.get("species", "")).strip():
        errors.append("'species' must not be blank")

    if "sunlight_needs" in data and not partial and not str(data.get("sunlight_needs", "")).strip():
        errors.append("'sunlight_needs' must not be blank")

    last_watered_at = None
    if "last_watered_at" in data and data["last_watered_at"] not in (None, ""):
        try:
            last_watered_at = _parse_datetime(data["last_watered_at"], "last_watered_at")
        except ValueError as exc:
            errors.append(str(exc))

    return errors, last_watered_at


@plants_bp.route("/plants", methods=["GET"])
def list_plants():
    plants = Plant.query.filter_by(active=True).order_by(Plant.created_at.desc()).all()
    result = [plant_with_schedule(p) for p in plants]
    db.session.commit()
    return jsonify(result)


@plants_bp.route("/plants/thirsty", methods=["GET"])
def list_thirsty_plants():
    plants = Plant.query.filter_by(active=True).all()
    result = [plant_with_schedule(p) for p in plants]
    db.session.commit()
    thirsty = [p for p in result if p["is_thirsty"]]
    return jsonify(thirsty)


@plants_bp.route("/plants/<int:plant_id>", methods=["GET"])
def get_plant(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    result = plant_with_schedule(plant)
    db.session.commit()
    return jsonify(result)


@plants_bp.route("/plants", methods=["POST"])
def create_plant():
    data = request.get_json(silent=True) or {}
    errors, last_watered_at = _validate_plant_payload(data)
    if errors:
        return jsonify({"errors": errors}), 400

    plant = Plant(
        name=data["name"].strip(),
        species=data["species"].strip(),
        watering_frequency_days=int(data["watering_frequency_days"]),
        sunlight_needs=data["sunlight_needs"].strip(),
        used_ai_suggestion=bool(data.get("used_ai_suggestion", False)),
        ai_explanation=data.get("ai_explanation"),
        ai_sources=data.get("ai_sources") or [],
        last_watered_at=last_watered_at,
        notes=data.get("notes"),
    )
    db.session.add(plant)
    db.session.flush()
    result = plant_with_schedule(plant)
    db.session.commit()
    return jsonify(result), 201


@plants_bp.route("/plants/<int:plant_id>", methods=["PUT"])
def update_plant(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    data = request.get_json(silent=True) or {}
    errors, last_watered_at = _validate_plant_payload(data, partial=True)
    if errors:
        return jsonify({"errors": errors}), 400

    if "name" in data:
        plant.name = data["name"].strip()
    if "species" in data:
        plant.species = data["species"].strip()
    if "watering_frequency_days" in data:
        plant.watering_frequency_days = int(data["watering_frequency_days"])
    if "sunlight_needs" in data:
        plant.sunlight_needs = data["sunlight_needs"].strip()
    if "used_ai_suggestion" in data:
        plant.used_ai_suggestion = bool(data["used_ai_suggestion"])
    if "ai_explanation" in data:
        plant.ai_explanation = data["ai_explanation"]
    if "ai_sources" in data:
        plant.ai_sources = data["ai_sources"]
    if last_watered_at is not None:
        plant.last_watered_at = last_watered_at
    if "notes" in data:
        plant.notes = data["notes"]

    result = plant_with_schedule(plant)
    db.session.commit()
    return jsonify(result)


@plants_bp.route("/plants/<int:plant_id>", methods=["DELETE"])
def delete_plant(plant_id):
    plant = Plant.query.get_or_404(plant_id)
    plant.active = False
    db.session.commit()
    return jsonify({"success": True})


@plants_bp.route("/plants/ai-suggest", methods=["POST"])
def ai_suggest():
    data = request.get_json(silent=True) or {}
    species = (data.get("species") or "").strip()
    if not species:
        return jsonify({"errors": ["'species' is required"]}), 400

    try:
        suggestion = get_care_suggestion(species)
    except AiLookupError as exc:
        return jsonify({"errors": [str(exc)]}), 502

    return jsonify(suggestion)
