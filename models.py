from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    return datetime.utcnow()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    google_sub = db.Column(db.Text, nullable=False, unique=True)
    email = db.Column(db.Text, nullable=False, unique=True)
    name = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }


class Plant(db.Model):
    __tablename__ = "plants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    species = db.Column(db.Text, nullable=False)
    watering_frequency_days = db.Column(db.Integer, nullable=False)
    sunlight_needs = db.Column(db.Text, nullable=False)
    used_ai_suggestion = db.Column(db.Boolean, nullable=False, default=False)
    ai_explanation = db.Column(db.Text, nullable=True)
    ai_sources = db.Column(db.JSON, nullable=True)
    last_watered_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    notes = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "species": self.species,
            "watering_frequency_days": self.watering_frequency_days,
            "sunlight_needs": self.sunlight_needs,
            "used_ai_suggestion": self.used_ai_suggestion,
            "ai_explanation": self.ai_explanation,
            "ai_sources": self.ai_sources or [],
            "last_watered_at": self.last_watered_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "notes": self.notes,
            "active": self.active,
        }


class ContactSettings(db.Model):
    __tablename__ = "contact_settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    phone_number = db.Column(db.Text, nullable=True)
    email = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "phone_number": self.phone_number,
            "email": self.email,
            "updated_at": self.updated_at.isoformat(),
        }


class WateringLog(db.Model):
    __tablename__ = "watering_log"

    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey("plants.id"), nullable=False)
    watered_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "plant_id": self.plant_id,
            "watered_at": self.watered_at.isoformat(),
        }


class NotificationsLog(db.Model):
    __tablename__ = "notifications_log"

    id = db.Column(db.Integer, primary_key=True)
    plant_id = db.Column(db.Integer, db.ForeignKey("plants.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    channel = db.Column(db.Text, nullable=False)
    digest_id = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "plant_id": self.plant_id,
            "user_id": self.user_id,
            "sent_at": self.sent_at.isoformat(),
            "channel": self.channel,
            "digest_id": self.digest_id,
        }
