# Test requirements that examine matched request context state

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

from flask import g
from flask_require import ContextRequire, ValueRequire


def test_context_state(app, client):
    """Test a requiement based on a value previously set in the request context"""

    @app.route("/fail1")
    def fail1():
        return "Bonjour"

    def test_and_save(value):
        g.temp = value
        return "X" in value

    @app.route("/test")
    @ValueRequire(("something", test_and_save), "fail1")
    @ContextRequire(("temp", "Xylophone"), "index")
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Bonjour"

    rv = client.get("/test?something=Trombone", follow_redirects=True)
    assert rv.text == "Bonjour"

    rv = client.get("/test?something=EXIT", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/test?something=Xylophone", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_context_never_set(app, client):
    """Test a context requiement for a value the doesn't exist"""

    @app.route("/test")
    @ContextRequire(("temp", "Xylophone"), "index")
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"
