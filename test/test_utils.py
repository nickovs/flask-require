# Test various utility functions

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

from flask_require import Require, up


def test_simple_redirect(app, client):
    """Test a simple requiement who's check always fail."""
    @app.route("/test")
    @Require(lambda: False, up)
    def test():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"
