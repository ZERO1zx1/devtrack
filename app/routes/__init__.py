"""Blueprint wiring — one function to attach every route module."""

from flask import Blueprint

from . import analytics, auth, main, projects, tasks


def register_blueprints(app):
    blueprints: list[Blueprint] = [
        main.create_blueprint(),
        auth.create_blueprint(),
        tasks.create_blueprint(),
        projects.create_blueprint(),
        analytics.create_blueprint(),
    ]
    for bp in blueprints:
        app.register_blueprint(bp)