# Test requirements on Blueprints

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

import pytest
from flask import request, Blueprint
from flask_require import Require


def test_blueprint_views(app, client):
    """Test requiements on views inside Blueprints."""
    bp1 = Blueprint("yin", __name__, url_prefix="/yin")
    bp2 = Blueprint("yang", __name__, url_prefix="/yang")

    @bp1.route("/test/")
    @Require(lambda: False, "index")
    def test1():
        return "Goodbye!"

    @bp2.route("/test/")
    @Require(lambda: True, "index")
    def test2():
        return "Goodbye!"

    app.register_blueprint(bp1)
    app.register_blueprint(bp2)

    rv = client.get("/yin/test", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/yang/test", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_blueprint_before_request(app, client):
    """Test requiements registered directly with Blueprints."""
    bp1 = Blueprint("yin", __name__, url_prefix="/yin")
    bp1.before_request(Require(lambda: False, "index"))
    bp2 = Blueprint("yang", __name__, url_prefix="/yang")
    bp2.before_request(Require(lambda: True, "index"))

    @bp1.route("/test/")
    def test1():
        return "Goodbye!"

    @bp2.route("/test/")
    def test2():
        return "Goodbye!"

    app.register_blueprint(bp1)
    app.register_blueprint(bp2)

    rv = client.get("/yin/test", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/yang/test", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_blueprint_before_request_bad_arg(app, client):
    """Test requiements registered directly with Blueprints."""
    bp1 = Blueprint("yin", __name__, url_prefix="/yin")
    bp1.before_request(Require(lambda x: x&1, "index"))

    @bp1.route("/test/")
    def test1():
        return "Goodbye!"

    app.register_blueprint(bp1)

    with pytest.raises(ValueError):
        rv = client.get("/yin/test", follow_redirects=True)
