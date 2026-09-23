"""
NetGuard AI — Flask Application Factory
"""
import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Flask

from .config import config_map
from .extensions import db, migrate


def create_app(config_name: str = "development") -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),
    )

    # Load config
    cfg = config_map.get(config_name, config_map["default"])
    app.config.from_object(cfg)
    cfg.init_app(app)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Set up logging
    _configure_logging(app)

    # Register blueprints
    from .blueprints.dashboard import dashboard_bp
    from .blueprints.analyze import analyze_bp
    from .blueprints.activities import activities_bp
    from .blueprints.alerts import alerts_bp
    from .blueprints.analytics import analytics_bp
    from .blueprints.dataset import dataset_bp
    from .blueprints.model_info import model_info_bp
    from .blueprints.reports import reports_bp
    from .blueprints.pages import pages_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(analyze_bp, url_prefix="/api")
    app.register_blueprint(activities_bp, url_prefix="/api")
    app.register_blueprint(alerts_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")
    app.register_blueprint(dataset_bp, url_prefix="/api")
    app.register_blueprint(model_info_bp, url_prefix="/api")
    app.register_blueprint(reports_bp, url_prefix="/api")

    # Create DB tables
    with app.app_context():
        db.create_all()
        app.logger.info("NetGuard AI started. Database initialized.")

    return app


def _configure_logging(app: Flask):
    log_dir = app.config.get("LOGS_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "netguard.log")

    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    file_handler.setFormatter(formatter)

    if not app.logger.handlers:
        app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
