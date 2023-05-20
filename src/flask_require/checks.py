# flask_require/checks.py

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

# pylint: disable=too-few-public-methods

"""A set of classes that encapsulate quick checks for values"""

import re
import time

from flask import g

_TIME_UNITS = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
    "w": 60 * 60 * 24 * 7,
    "M": 60 * 60 * 24 * 30,
    "y": 60 * 60 * 24 * 365,
}


class TimeStampAge:
    """A callable class to check the age of the timestamp"""
    def __init__(self, age):
        """
        :param age: either an interger number of seconds or a string of an interger count
            followed by one of "s", "m", "h", "d", "w", "M" or "y" for units of second, minute,
            hour, day, week, month (30 days) or year (365 days) respectively.
        """
        if isinstance(age, str):
            match = re.match(r"(\d+)([smhdwMy])?\s*$", age)
            if not match:
                raise ValueError("Malformed timestamp age string")
            count, unit = match.groups()
            age = float(count) * _TIME_UNITS[unit]
        elif not isinstance(age, (int, float)):
            raise ValueError("Timestamp age must be a number or a string of a number and unit")

        self._age = age

    def __call__(self, timestamp):
        # Return if the timestamp is less than self._age old
        now = time.time()
        return timestamp + self._age >= now


class Contains:
    """A callable to check if a value is a list or tuple that contains a specific value"""
    def __init__(self, required_value):
        self._required = required_value

    def __call__(self, value):
        return isinstance(value, (set, list, tuple)) and self._required in value


class MatchContext:
    """A callable to check if a value is the same as the value stored under some key
    in the request global"""
    def __init__(self, global_key):
        self._key = global_key

    def __call__(self, value):
        return value == getattr(g, self._key, None)
