# Test requirements based on request values

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

from flask_require import ValueRequire


def test_simple_value(app, client):
    """Test a requiement based on request value"""
    @app.route("/test")
    @ValueRequire(("something", "yin"), "index")
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/test?something=yin", follow_redirects=True)
    assert rv.text == "Goodbye!"

    rv = client.get("/test?something=yang", follow_redirects=True)
    assert rv.text == "Hello"


def test_value_multiple_options(app, client):
    """Test a requiement based on request value being an item in a list"""
    @app.route("/test")
    @ValueRequire(("something", ["yin", "yang"]), "index")
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/test?something=yin", follow_redirects=True)
    assert rv.text == "Goodbye!"

    rv = client.get("/test?something=yang", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_multiple_values(app, client):
    """Test a requiement based on multiple request values"""
    @app.route("/test")
    @ValueRequire([
        ("thing1", ["yin", "yang"]),
        ("thing2", ["red", "blue"])
        ], "index")
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/test?thing1=yin", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/test?thing2=blue", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/test?thing1=yin&thing2=blue", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_values_with_callable(app, client):
    """Test a requiement based on checking a request value with a callable"""
    @app.route("/test")
    @ValueRequire(("something", lambda x: "x" in x.lower()), "index")
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/test?something=abc", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/test?something=XYZ", follow_redirects=True)
    assert rv.text == "Goodbye!"
