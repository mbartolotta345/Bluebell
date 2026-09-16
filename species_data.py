"""Built-in reference data for popular houseplants.

Populate SPECIES with one dict per plant, shaped like:

    {
        "name": "Snake Plant",
        "watering_frequency_days": 14,
        "sunlight_needs": "Low to bright indirect light",
        "description": "Very drought-tolerant; let soil dry out completely between waterings.",
        "source_url": "https://example.com/snake-plant-care",
    }

`seed_species(db, SpeciesGuide)` upserts this list into the database by
`name` (case-sensitive match) - safe to call every time the app starts.
Editing an entry here and restarting the app updates the stored row; it
does not touch any plant a user has already saved with those values.
"""

SPECIES = []


def seed_species(db, SpeciesGuide):
    if not SPECIES:
        return

    existing = {s.name: s for s in SpeciesGuide.query.all()}

    for entry in SPECIES:
        row = existing.get(entry["name"])
        if row is None:
            db.session.add(SpeciesGuide(**entry))
        else:
            row.watering_frequency_days = entry["watering_frequency_days"]
            row.sunlight_needs = entry["sunlight_needs"]
            row.description = entry["description"]
            row.source_url = entry["source_url"]

    db.session.commit()
