# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

"""Test fixtures, as per Flask's own test cases"""
import os

import pytest as pytest
from flask import Flask


@pytest.fixture
def app():
    app = Flask("flask_test", root_path=os.path.dirname(__file__))
    app.config.update(
        TESTING=True,
        SECRET_KEY="test key",
    )

    @app.route("/")
    def index():
        return "Hello"

    return app


@pytest.fixture
def client(app):
    return app.test_client()
