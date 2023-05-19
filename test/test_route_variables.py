# Test requirements that examine matched route variables

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

import pytest

from flask_require import Require


def test_simple_route_variable(app, client):
    @app.route('/foo/<name>')
    @Require(lambda name: (name.find("X") != -1), "index")
    def test(name):
        return f"{name} has an X!"

    rv = client.get("/foo/bar", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/foo/Xylophone", follow_redirects=True)
    assert rv.text == "Xylophone has an X!"


def test_multiuple_route_variables(app, client):
    @app.route('/foo/<int:first>/<int:second>')
    @Require(lambda first, second: (first > second), "index")
    def test(first, second):
        return f"{first} > {second}"

    rv = client.get("/foo/1/2", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/foo/2/1", follow_redirects=True)
    assert rv.text == "2 > 1"


def test_multiuple_route_variables_reversed(app, client):
    @app.route('/foo/<int:first>/<int:second>')
    @Require(lambda second, first: (first > second), "index")
    def test(first, second):
        return f"{first} > {second}"

    rv = client.get("/foo/1/2", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/foo/2/1", follow_redirects=True)
    assert rv.text == "2 > 1"


def test_subset_route_variables(app, client):
    @app.route('/foo/<int:first>/<int:second>')
    @Require(lambda second: second % 2, "index")
    def test(first, second):
        return f"{first}, {second}"

    rv = client.get("/foo/1/1", follow_redirects=True)
    assert rv.text == "1, 1"

    rv = client.get("/foo/1/2", follow_redirects=True)
    assert rv.text == "Hello"

    rv = client.get("/foo/2/1", follow_redirects=True)
    assert rv.text == "2, 1"

    rv = client.get("/foo/2/2", follow_redirects=True)
    assert rv.text == "Hello"


def test_bad_route_variable(app, client):
    with pytest.raises(ValueError):
        @app.route('/foo/<name>')
        @Require(lambda not_name: (not_name.find("X") != -1), "index")
        def test(name):
            return f"{name} has an X!"
