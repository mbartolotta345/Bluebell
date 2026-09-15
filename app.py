import os

from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()

from models import db  # noqa: E402
from routes.contact import contact_bp  # noqa: E402
from routes.plants import plants_bp  # noqa: E402

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "plants.db")


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DB_PATH}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    app.register_blueprint(plants_bp)
    app.register_blueprint(contact_bp)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


app = create_app()

if __name__ == "__main__":
    if os.environ.get("ENABLE_SCHEDULER", "false").lower() == "true":
        from scheduler import start_scheduler

        start_scheduler(app)
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(debug=debug, port=int(os.environ.get("PORT", 5000)))
