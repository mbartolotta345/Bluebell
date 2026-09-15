import os

from flask import Blueprint, jsonify, request, session
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from models import User, db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/google", methods=["POST"])
def google_login():
    data = request.get_json(silent=True) or {}
    credential = data.get("credential")
    if not credential:
        return jsonify({"errors": ["Missing Google credential."]}), 400

    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    if not client_id:
        return jsonify({"errors": ["GOOGLE_OAUTH_CLIENT_ID is not configured on the server."]}), 500

    try:
        payload = google_id_token.verify_oauth2_token(
            credential, google_requests.Request(), client_id
        )
    except ValueError as exc:
        return jsonify({"errors": [f"Invalid Google credential: {exc}"]}), 401

    google_sub = payload["sub"]
    email = payload.get("email")
    name = payload.get("name")

    user = User.query.filter_by(google_sub=google_sub).first()
    if user is None:
        user = User(google_sub=google_sub, email=email, name=name)
        db.session.add(user)
    else:
        user.email = email
        user.name = name
    db.session.commit()

    session["user_id"] = user.id
    return jsonify(user.to_dict())


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"success": True})


@auth_bp.route("/auth/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"logged_in": False})

    user = User.query.get(user_id)
    if not user:
        session.pop("user_id", None)
        return jsonify({"logged_in": False})

    return jsonify({"logged_in": True, **user.to_dict()})
