# Basic test cases

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

import pytest
from flask import request
from flask_require import Require


def test_simple_redirect(app, client):
    """Test a simple requiement who's check always fail."""
    @app.route("/test")
    @Require(lambda: False, "index")
    def test():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"


def test_redirect_if_query(app, client):
    """Test a simple requiement who's check always fail."""
    @app.route("/test")
    @Require(lambda: "test" in request.values, "index")
    def test():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/test?test=foo", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_simple_redirect_bad_function(app, client):
    """Test a simple requiement who's check always fail."""
    with pytest.raises(ValueError):
        @app.route("/test")
        @Require("Not a function", "index")
        def test():
            return "Goodbye!"

def test_simple_direct_call_require():
    req1 = Require(lambda: True, "index")
    req2 = Require(lambda x: bool(x & 1), "index")

    assert req1.check() == True
    assert req2.check(x=0) == False
    assert req2.check(x=47) == True
