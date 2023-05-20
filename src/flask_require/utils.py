# flask_require/utils.py

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

# pylint: disable=invalid-name

"""General utility functions"""

from flask import request


def up():
    """Return the path to the node one level up from the current view"""
    current_path = request.path
    last_slash = current_path.rfind("/", 0, -1)
    if last_slash >= 0:
        current_path = current_path[:last_slash+1]
    return request.root_path + current_path
