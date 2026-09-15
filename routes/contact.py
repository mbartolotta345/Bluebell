from flask import Blueprint, jsonify, request

from models import ContactSettings, db

contact_bp = Blueprint("contact", __name__)


def _get_or_create_settings():
    settings = ContactSettings.query.first()
    if settings is None:
        settings = ContactSettings(phone_number=None, email=None)
        db.session.add(settings)
        db.session.commit()
    return settings


@contact_bp.route("/contact", methods=["GET"])
def get_contact():
    settings = _get_or_create_settings()
    return jsonify(settings.to_dict())


@contact_bp.route("/contact", methods=["PUT"])
def update_contact():
    settings = _get_or_create_settings()
    data = request.get_json(silent=True) or {}

    if "phone_number" in data:
        settings.phone_number = data["phone_number"] or None
    if "email" in data:
        settings.email = data["email"] or None

    db.session.commit()
    return jsonify(settings.to_dict())
