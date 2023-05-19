# Test requirements based on session state

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

import time
import pytest

from flask import g
from flask_require import SessionRequire, TimeStampAge, Contains, MatchContext


def test_simple_session_state(app, client):
    """Test a requiement based on session state"""
    @app.route("/test")
    @SessionRequire(("something", "yin"), "index")
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['something'] = "yin"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Goodbye!"

    with client.session_transaction() as session:
        session['something'] = "yang"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"


def test_multiple_session_state(app, client):
    """Test a requiement based on multiple session states"""
    @app.route("/test")
    @SessionRequire(
        [("something", "yin"), ("else", "yang")],
        "index"
    )
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['something'] = "yin"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['else'] = "yang"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_session_state_present(app, client):
    """Test a requiement based on session state"""
    @app.route("/test")
    @SessionRequire("something", "index")
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['something'] = "anything"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_session_state_value_in_list(app, client):
    """Test a requiement based on session state"""
    @app.route("/test")
    @SessionRequire(("something", ['foo', 'bar']), "index")
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['something'] = "bar"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_session_state_check_function(app, client):
    """Test a requiement based on session state"""
    @app.route("/test")
    @SessionRequire(("something", lambda x: x.find("x") != -1), "index")
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['something'] = "bar"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['something'] = "barxbar"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_bad_session_require():
    with pytest.raises(ValueError):
        _ = SessionRequire(("foo", 1, 2), "index")

    with pytest.raises(ValueError):
        _ = SessionRequire([("foo", 1, 2), ("bar", 1)], "index")

    with pytest.raises(ValueError):
        _ = SessionRequire(1, "index")

    with pytest.raises(ValueError):
        _ = SessionRequire((1, "foo"), "index")


def test_session_state_contains(app, client):
    """Test a requiement based on a session state value containing a value"""
    @app.route("/test")
    @SessionRequire(("ingredients", Contains("spam")), "index")
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['ingredients'] = ['egg', 'sausage']

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['ingredients'] = ['egg', 'sausage', 'spam', 'chips']

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_session_state_timeout(app, client):
    """Test a requiement based on a session state containing a timestamp"""
    test_set = [
        ("raw_seconds", 17, 17),
        ("string_seconds", "5s", 5),
        ("minutes", "3m", 180),
        ("hours", "2h", 7200),
        ("days", "1d", 86400),
        ("weeks", "2w", 1209600),
        ("months", "1M", 2592000),
        ("years", "1y", 31536000)
    ]

    time_times = [duration + delta for _, _, duration in test_set for delta in [-1, 1]]

    for path, check_time, _ in test_set:
        @SessionRequire(("timestamp", TimeStampAge(check_time)), "index")
        def farewell():
            return "Goodbye!"

        app.add_url_rule("/" + path, endpoint=path, view_func=farewell)

    for path, _, duration in test_set:
        for t in time_times:
            with client.session_transaction() as session:
                session['timestamp'] = time.time() - t

            rv = client.get("/"+path, follow_redirects=True)
            assert rv.text == "Hello" if t >= duration else "Goodbye!"


def test_session_timeout_errors():
    with pytest.raises(ValueError):
        _ = TimeStampAge("check_time")

    with pytest.raises(ValueError):
        _ = TimeStampAge([1, 2])


def test_session_match_global(app, client):
    """Test a requirement that session state matches some global state"""
    @app.route("/test")
    @SessionRequire(("session_key", MatchContext("global_key")), "index")
    def farewell():
        return "Goodbye!"

    with app.app_context():
        rv = client.get("/test", follow_redirects=True)
        assert rv.text == "Hello"

        with client.session_transaction() as session:
            session['session_key'] = "spam"

        rv = client.get("/test", follow_redirects=True)
        assert rv.text == "Hello"

        g.global_key = "spam"

        rv = client.get("/test", follow_redirects=True)
        assert rv.text == "Goodbye!"
