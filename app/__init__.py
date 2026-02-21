from flask import Flask
from config.settings import Config
from app.extensions import db, jwt, bcrypt, cors, swagger
from app.middleware.auth import register_middleware


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Init extensions ────────────────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    swagger.init_app(app)

    # ── Register middleware hooks ───────────────────────────────────────────────
    register_middleware(app)

    # ── Register blueprints ────────────────────────────────────────────────────
    from app.routes.auth import auth_bp
    from app.routes.tasks import tasks_bp
    from app.routes.reminders import reminders_bp
    from app.routes.notes import notes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(notes_bp)

    # ── Create DB tables ───────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    # ── Start scheduler ────────────────────────────────────────────────────────
    from app.utils.scheduler import start_scheduler
    start_scheduler(app)

    return app