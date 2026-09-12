"""DevTrack entry point.

Boots the application through the factory in ``app/__init__.py``.
Uses :class:`~config.DevConfig` by default (see ``CONFIG`` env var).
"""

import os

from app import create_app

app = create_app(os.environ.get("CONFIG", "development"))


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))