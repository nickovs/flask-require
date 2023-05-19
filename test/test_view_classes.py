# Testing requirements applies to view classes and their methods

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

import pytest
from flask import request
from flask.views import View, MethodView
from flask_require import Require


def test_simple_view_class(app, client):
    requirement = Require(lambda: "test" in request.values, "index")

    class MyView(View):
        decorators = [requirement]

        def dispatch_request(self):
            return "Goodbye!"

    app.add_url_rule("/test/", view_func=MyView.as_view("test"))

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/test?test=foo", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_view_class_bad_arg(app, client):
    requirement = Require(lambda x: (x & 1) in request.values, "index")

    class MyView(View):
        decorators = [requirement]

        def dispatch_request(self):
            return "Goodbye!"

    with pytest.raises(ValueError):
        app.add_url_rule("/test/", view_func=MyView.as_view("test"))


def test_simple_method_view_class(app, client):
    class MyMethodView(MethodView):
        @Require(lambda: "test" in request.values, "index")
        def get(self):
            return "GOT"

        def post(self):
            return "POSTED"

    app.add_url_rule("/test/", view_func=MyMethodView.as_view("test"))

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/test?test=foo", follow_redirects=True)
    assert rv.text == "GOT"

    rv = client.post("/test", follow_redirects=True)
    assert rv.text == "POSTED"

    rv = client.post("/test?test=foo", follow_redirects=True)
    assert rv.text == "POSTED"
