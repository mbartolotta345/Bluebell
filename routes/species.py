from flask import Blueprint, jsonify

from models import SpeciesGuide

species_bp = Blueprint("species", __name__)


@species_bp.route("/species", methods=["GET"])
def list_species():
    species = SpeciesGuide.query.order_by(SpeciesGuide.name).all()
    return jsonify([s.to_dict() for s in species])
