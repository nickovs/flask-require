# flask-require

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

"""flask-require: Easier decorators for Flask view access control"""

from .checks import MatchContext, TimeStampAge, Contains
from .require import Require, SessionRequire, ValueRequire, ContextRequire, AllRequire, AnyRequire
from .utils import up

__version__ = "0.2.0"

__all__ = [
    "Require", "SessionRequire", "ValueRequire", "ContextRequire", "AllRequire", "AnyRequire",
    "MatchContext", "TimeStampAge", "Contains", "up"
]
