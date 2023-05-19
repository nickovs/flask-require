# Test requirements that post 'flash' messages

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

from flask import get_flashed_messages, json
from flask_require import Require, SessionRequire, AnyRequire, AllRequire


def add_json_dump(app):
    @app.route("/dump")
    def dump():
        msgs = get_flashed_messages(with_categories=True)
        return json.dumps({"msgs": msgs})


def test_simple_flash(app, client):
    """Test a flashed message from a requiement who's check always fail."""
    add_json_dump(app)

    @app.route("/test")
    @Require(lambda: False, "dump", "Always fails")
    def test():
        return json.dumps({})

    rv = client.get("/test", follow_redirects=True)
    assert json.loads(rv.text) == {'msgs': [['warning', 'Always fails']]}


def test_flash_category(app, client):
    """Test a flashed message with a message category."""
    add_json_dump(app)

    @app.route("/test")
    @Require(lambda: False, "dump", "Always fails", "error")
    def test():
        return json.dumps({})

    rv = client.get("/test", follow_redirects=True)
    assert json.loads(rv.text) == {'msgs': [["error", "Always fails"]]}


def test_flash_compound_and(app, client):
    """Test the flashed message from a compound AND requirement"""
    add_json_dump(app)

    req1 = SessionRequire(("a", "A"), "dump", "Fail A")
    req2 = SessionRequire(("b", "B"), "dump", "Fail B")
    compound_req = req1 & req2

    @app.route("/test")
    @compound_req
    def test():
        return json.dumps({})

    rv = client.get("/test", follow_redirects=True)
    assert json.loads(rv.text) == {'msgs': [['warning', 'Fail A']]}

    with client.session_transaction() as session:
        session['a'] = "A"

    rv = client.get("/test", follow_redirects=True)
    assert json.loads(rv.text) == {'msgs': [['warning', 'Fail B']]}

    with client.session_transaction() as session:
        session['b'] = "B"

    rv = client.get("/test", follow_redirects=True)
    assert json.loads(rv.text) == {}


def test_flash_compound_or(app, client):
    """Test the flashed message from a compound OR requirement"""

    add_json_dump(app)

    req1 = SessionRequire(("a", "A"), "dump", "Fail A")
    req2 = SessionRequire(("b", "B"), "dump", "Fail B")
    compound_req = req1 | req2

    @app.route("/test")
    @compound_req
    def test():
        return json.dumps({})

    rv = client.get("/test", follow_redirects=True)
    assert json.loads(rv.text) == {'msgs': [['warning', 'Fail A']]}

    with client.session_transaction() as session:
        session['a'] = "A"

    rv = client.get("/test", follow_redirects=True)
    assert json.loads(rv.text) == {}

    with client.session_transaction() as session:
        session['a'] = None
        session['b'] = "B"

    rv = client.get("/test", follow_redirects=True)
    assert json.loads(rv.text) == {}


def test_compound_different_flash(app, client):
    """Test a requiement based on multiple session states"""
    add_json_dump(app)

    req1 = SessionRequire(("a", "A"), "index", "req1", "error")
    req2 = SessionRequire(("b", "B"), "index", "req2", "error")

    compound_req_or = AnyRequire(req1, req2,
                                 redirect_endpoint="dump",
                                 flash_msg="OR", msg_category="warning")
    compound_req_and = AllRequire(req1, req2,
                                  redirect_endpoint="dump",
                                  flash_msg="AND", msg_category="warning")

    @app.route("/test_or")
    @compound_req_or
    def farewell1():
        return "Goodbye!"

    @app.route("/test_and")
    @compound_req_and
    def farewell2():
        return "Goodbye!"

    rv = client.get("/test_or", follow_redirects=True)
    assert json.loads(rv.text) == {'msgs': [['warning', 'OR']]}

    rv = client.get("/test_and", follow_redirects=True)
    assert json.loads(rv.text) == {'msgs': [['warning', 'AND']]}

    with client.session_transaction() as session:
        session['a'] = "A"
        session['b'] = "B"

    rv = client.get("/test_or", follow_redirects=True)
    assert rv.text == "Goodbye!"

    rv = client.get("/test_and", follow_redirects=True)
    assert rv.text == "Goodbye!"
