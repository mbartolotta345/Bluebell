from flask import Blueprint, jsonify, request

from models import ContactSettings, db
from utils import current_user_id, login_required

contact_bp = Blueprint("contact", __name__)


def _get_or_create_settings():
    user_id = current_user_id()
    settings = ContactSettings.query.filter_by(user_id=user_id).first()
    if settings is None:
        settings = ContactSettings(user_id=user_id, phone_number=None, email=None)
        db.session.add(settings)
        db.session.commit()
    return settings


@contact_bp.route("/contact", methods=["GET"])
@login_required
def get_contact():
    settings = _get_or_create_settings()
    return jsonify(settings.to_dict())


@contact_bp.route("/contact", methods=["PUT"])
@login_required
def update_contact():
    settings = _get_or_create_settings()
    data = request.get_json(silent=True) or {}

    if "phone_number" in data:
        settings.phone_number = data["phone_number"] or None
    if "email" in data:
        settings.email = data["email"] or None

    db.session.commit()
    return jsonify(settings.to_dict())
