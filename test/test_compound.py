# Test compound requirements

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

from operator import __and__, __or__

import pytest
from flask_require import SessionRequire, AnyRequire, AllRequire


def test_compound_and(app, client):
    """Test a requiement based on multiple session states"""
    req1 = SessionRequire(("a", "A"), "index")
    req2 = SessionRequire(("b", "B"), "index")
    compound_req = req1 & req2

    @app.route("/test")
    @compound_req
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['a'] = "A"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['b'] = "B"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_compound_or(app, client):
    """Test a requiement based on multiple session states"""
    req1 = SessionRequire(("a", "A"), "index")
    req2 = SessionRequire(("b", "B"), "index")
    compound_req = req1 | req2

    @app.route("/test")
    @compound_req
    def farewell():
        return "Goodbye!"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Hello"

    with client.session_transaction() as session:
        session['a'] = "A"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Goodbye!"

    with client.session_transaction() as session:
        session['a'] = None
        session['b'] = "B"

    rv = client.get("/test", follow_redirects=True)
    assert rv.text == "Goodbye!"


def test_compound_multiway(app, client):
    """Test a requiement based on multiple session states"""
    req1 = SessionRequire(("a", "A"), "index")
    req2 = SessionRequire(("b", "B"), "index")
    req3 = SessionRequire(("c", "C"), "index")

    test_set = [
        ((req1 & (req2 & req3)), lambda aa, bb, cc: aa and (bb and cc)),
        ((req1 | (req2 | req3)), lambda aa, bb, cc: aa or (bb or cc)),
        (((req1 & req2) & req3), lambda aa, bb, cc: (aa and bb) and cc),
        (((req1 | req2) | req3), lambda aa, bb, cc: (aa or bb) or cc),
        ((req1 | (req2 & req3)), lambda aa, bb, cc: aa or (bb and cc)),
        ((req1 & (req2 | req3)), lambda aa, bb, cc: aa and (bb or cc)),
        (((req1 | req2) & req3), lambda aa, bb, cc: (aa or bb) and cc),
        (((req1 & req2) | req3), lambda aa, bb, cc: (aa and bb) or cc),
    ]

    for i, (requirement, checker) in enumerate(test_set):
        name = f"test_{i}"

        @requirement
        def farewell():
            return "Goodbye!"

        app.add_url_rule("/" + name, endpoint=name, view_func=farewell)

    for i in range(len(test_set)):
        for a in ['', 'A']:
            for b in ['', 'B']:
                for c in ['', 'C']:
                    with client.session_transaction() as session:
                        session['a'] = a
                        session['b'] = b
                        session['c'] = c

                    path = f"/test_{i}"
                    checker = test_set[i][1]
                    rv = client.get(path, follow_redirects=True)

                    assert rv.text == ("Goodbye!" if checker(a, b, c) else "Hello")


def test_compound_four_way(app, client):
    """Test a requiement based on multiple session states"""
    req1 = SessionRequire(("x", lambda x: x & 1), "index")
    req2 = SessionRequire(("x", lambda x: x & 2), "index")
    req3 = SessionRequire(("x", lambda x: x & 4), "index")
    req4 = SessionRequire(("x", lambda x: x & 8), "index")

    def checker(x, pattern):
        ops = {
            "&": __and__,
            "|": __or__
        }
        bits = [bool(j & (1 << i)) for i in range(4)]
        return ops[pattern[1]](
            ops[pattern[0]](bits[0], bits[1]),
            ops[pattern[2]](bits[2], bits[3])
        )

    test_set = [
        (((req1 & req2) & (req3 & req4)), "&&&"),
        (((req1 | req2) & (req3 & req4)), "|&&"),
        (((req1 & req2) | (req3 & req4)), "&|&"),
        (((req1 | req2) | (req3 & req4)), "||&"),
        (((req1 & req2) & (req3 | req4)), "&&|"),
        (((req1 | req2) & (req3 | req4)), "|&|"),
        (((req1 & req2) | (req3 | req4)), "&||"),
        (((req1 | req2) | (req3 | req4)), "|||"),
    ]

    for i, (requirement, pattern) in enumerate(test_set):
        name = f"test_{i}"

        @requirement
        def farewell():
            return "Goodbye!"

        app.add_url_rule("/" + name, endpoint=name, view_func=farewell)

    for i in range(len(test_set)):
        for j in range(16):
            with client.session_transaction() as session:
                session['x'] = j

            path = f"/test_{i}"
            pattern = test_set[i][1]
            rv = client.get(path, follow_redirects=True)

            assert rv.text == ("Goodbye!" if checker(j, pattern) else "Hello")


def test_compound_errors_bad_rhs():
    req1 = SessionRequire(('foo', 1), "index")
    req2 = SessionRequire(('bar', 1), "index")

    req_and = req1 & req2
    req_or = req1 | req2

    with pytest.raises(ValueError):
        _ = req_and & True

    with pytest.raises(ValueError):
        _ = req_or & True

    with pytest.raises(ValueError):
        _ = req_and | True

    with pytest.raises(ValueError):
        _ = req_or | True


def test_compound_empty():
    req = SessionRequire(('foo', 1), "index")

    with pytest.raises(ValueError):
        _ = AnyRequire()

    with pytest.raises(ValueError):
        _ = AnyRequire(lambda x: x%2)

    with pytest.raises(ValueError):
        _ = AnyRequire(req, lambda x: x%2)
