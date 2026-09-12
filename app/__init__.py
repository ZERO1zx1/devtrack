"""DevTrack application package (Application Factory pattern).

The factory decouples configuration from creation so tests can inject a
temporary database and the dev/prod configs can differ cleanly.
"""

import os

from config import get_config
from flask import Flask


def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config(config_name))
    if os.environ.get("DATABASE"):
        app.config["DATABASE"] = os.environ["DATABASE"]

    from .extensions import csrf, db, login_manager

    db.init_app(app)
    login_manager.init_app(app)
    if csrf is not None:
        csrf.init_app(app)

    from .errors import register_error_handlers
    from .routes import register_blueprints

    register_blueprints(app)
    register_error_handlers(app)

    from .models import init_db

    with app.app_context():
        init_db()

    return app