# Test different types of redirecton generator

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

from flask_require import Require


def test_redirect_view_name(app, client):
    """Test a simple requiement who's check always fail."""
    @app.route("/test")
    @Require(lambda: False, "index")
    def test():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"


def test_redirect_url_path(app, client):
    """Test a simple requiement who's check always fail."""
    @app.route("/test")
    @Require(lambda: False, "/")
    def test():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"


def test_redirect_view_name(app, client):
    """Test a simple requiement who's check always fail."""

    def my_url():
        return "/"

    @app.route("/test")
    @Require(lambda: False, my_url)
    def test():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"


