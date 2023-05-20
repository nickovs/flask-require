# flask_require/require.py

# Copyright 2023 Nicko van Someren
# SPDX: MIT
# See LICENSE.md for the full license text.

# pylint: disable=invalid-name,no-else-return,too-few-public-methods

"""The core Require class and its subclasses"""

import re
from functools import wraps
from inspect import signature
from typing import Callable, List

from flask import flash, request, redirect, url_for, session, g

IS_HTTP = re.compile("^https?:")

# This is passed as a dummy handler when calling the check() method directly
_NO_HANDLER = object()


class BaseRequire:
    """The base class of requirement decorators. Do not use this class directly"""
    def __init__(self, redirect_endpoint=None, flash_msg=None, msg_category='warning'):
        self._redirect = redirect_endpoint
        self._msg = flash_msg
        self._msg_cat = msg_category
        self._check_args = set()

    def __call__(self, handler=None):
        # If this is called with a handler then it's being used as a decorator, in which case
        # this call wraps the handler and returns a new function.
        # If there is no handler then it's being called as a `before_request` function
        # so perform the checks, returning None if they pass and a response if they do not.

        if handler:
            # Make sure that the handler is going to be passed the arguments we need
            handler_sig = signature(handler)
            if any(arg_name not in handler_sig.parameters for arg_name in self._check_args):
                raise ValueError("Handler does not take arguments needed by check function")

            @wraps(handler)
            def wrapper(*args, **kwargs):
                x_ok, x_message, x_catagory, x_target = self._perform_checks(handler, args, kwargs)
                if not x_ok:
                    return self._handle_response(x_message, x_catagory, x_target)
                else:
                    return handler(*args, **kwargs)

            return wrapper
        else:
            # When called directly no arguments can be passed
            if self._check_args:
                raise ValueError("Require checks take arguments and can't be used directly")
            ok, message, catagory, target = self._perform_checks(_NO_HANDLER, None, None)
            return None if ok else self._handle_response(message, catagory, target)

    @staticmethod
    def _handle_response(message, catagory, target):
        if message is not None:
            flash(message, catagory)

        if isinstance(target, Callable):
            # Callables are called to give a URL
            return redirect(target())
        if target[0] == '/' or IS_HTTP.match(target):
            # Things that look like paths or URLs are passed directly
            return redirect(target)
        else:
            # Otherwise treat it as a view path.
            return redirect(url_for(target))

    def _perform_checks(self, handler, args, kwargs):  # pragma: no cover
        raise NotImplementedError

    def __and__(self, other):
        if not isinstance(other, BaseRequire):
            raise ValueError("rhs value must be another requirement")
        return AllRequire(self, other)

    def __or__(self, other):
        if not isinstance(other, BaseRequire):
            raise ValueError("rhs value must be another requirement")
        return AnyRequire(self, other)

    def check(self, **kwargs):
        """Perform the checks as a function, rather than a decorator"""
        ok, _, _, _ = self._perform_checks(_NO_HANDLER, [], kwargs)
        return ok


class Require(BaseRequire):
    """A simple requirement decorator that calls a funciton to performs a check.
    If the check fails then the view is redirected. Optionally a 'flash' message can be added.
    """
    def __init__(self, check_function, redirect_endpoint, flash_msg=None, msg_category='warning'):
        """
        :param check_function: a callable that needs to return True for processing to proceed
        :param redirect_endpoint: the view name, path or URL target if the check fails
        :param flash_msg: an optional message to flash to the user
        :param msg_category: an optional catagory for the flashed message
        """
        if not isinstance(check_function, Callable):
            raise ValueError("check_function must be callable")

        super().__init__(redirect_endpoint, flash_msg, msg_category)

        self._check_fn = check_function
        check_sig = signature(check_function)
        self._check_args |= set(check_sig.parameters.keys())

    def _perform_checks(self, handler, args, kwargs):
        if self._check_args:
            if handler is _NO_HANDLER:
                bound_args = kwargs
            else:
                handler_sig = signature(handler)
                bound_args = handler_sig.bind(*args, **kwargs).arguments
            bound_check_args = {name: bound_args[name] for name in self._check_args}
            OK = self._check_fn(**bound_check_args)
        else:
            OK = self._check_fn()

        return OK, self._msg, self._msg_cat, self._redirect


class KeyCheckRequire(BaseRequire):
    """A parent class for Value, Session and Context requirements"""
    def __init__(self, needs, redirect_endpoint, flash_msg=None, msg_category='warning'):
        """
        :param needs: Either a single item or a list of items, each of which may either be
            the name of a key to check or a tuple of a key name and a check, where the check
            may be a single value, a list of acceptable values or a callable that takes the
            value and returns True if the value is acceptable.
        :param redirect_endpoint: the view name, path or URL target if the check fails
        :param flash_msg: an optional message to flash to the user
        :param msg_category: an optional catagory for the flashed message
        """
        super().__init__(redirect_endpoint, flash_msg, msg_category)

        if not isinstance(needs, List):
            needs = [needs]

        for n in needs:
            if isinstance(n, tuple):
                if len(n) != 2:
                    raise ValueError("Requirement tuples must be length 2")
                key, _ = n
                if not isinstance(key, str):
                    raise ValueError("Session keys must be strings")
            elif not isinstance(n, str):
                raise ValueError("Session keys must be strings")

        self._needs = needs

    @staticmethod
    def _contains_key(key):  # pragma: no cover
        raise NotImplementedError

    @staticmethod
    def _fetch_key(key):  # pragma: no cover
        raise NotImplementedError

    def _check_single(self, requirement):
        if isinstance(requirement, tuple):

            key, value = requirement
            if not self._contains_key(key):
                return False

            container_value = self._fetch_key(key)

            if isinstance(value, List):
                return container_value in value
            elif isinstance(value, Callable):
                return value(container_value)
            else:
                return value == container_value
        else:
            return self._contains_key(requirement) and self._fetch_key(requirement) is not None

    def _perform_checks(self, handler, args, kwargs):
        _, _, _ = handler, args, kwargs
        OK = all(self._check_single(requirement) for requirement in self._needs)
        return OK, self._msg, self._msg_cat, self._redirect


class SessionRequire(KeyCheckRequire):
    """A class that checks conditions in the current Flask sessions.
    If the conditions are not met then a redirect reply is sent to send
    the user to the given URL. Optionally a 'flash' message can be added."""
    @staticmethod
    def _contains_key(key):  # pragma: no cover
        return key in session

    @staticmethod
    def _fetch_key(key):  # pragma: no cover
        return session[key]


class ValueRequire(KeyCheckRequire):
    """A class that checks conditions in the values in the current Flask request.
    If the conditions are not met then a redirect reply is sent to send
    the user to the given URL. Optionally a 'flash' message can be added."""
    @staticmethod
    def _contains_key(key):  # pragma: no cover
        return key in request.values

    @staticmethod
    def _fetch_key(key):  # pragma: no cover
        return request.values[key]


class ContextRequire(KeyCheckRequire):
    """A class that checks conditions in the current global request context :code:`flask.g`.
    If the conditions are not met then a redirect reply is sent to send
    the user to the given URL. Optionally a 'flash' message can be added."""
    @staticmethod
    def _contains_key(key):  # pragma: no cover
        return hasattr(g, key)

    @staticmethod
    def _fetch_key(key):  # pragma: no cover
        return getattr(g, key)


class CompoundRequire(BaseRequire):
    """A base class for all compound """
    def __init__(self, *sub_reqs: BaseRequire,
                 redirect_endpoint=None, flash_msg=None, msg_category=None):
        """
        :param sub_reqs: requirements that will be tested, in order from left to right
        :param redirect_endpoint: if provided then failure of the compound test will
            redirect to this endpoint instead of the endpoint associated with the first
            test that failed
        :param flash_msg: a flash message that overrides any message in the first test
            that failed
        :param msg_category: a catagory for the flash message
        """
        super().__init__(redirect_endpoint, flash_msg, msg_category)

        if not sub_reqs:
            raise ValueError("Requirements list must not be empty")

        if not all(isinstance(r, BaseRequire) for r in sub_reqs):
            raise ValueError("All parameters must be requirements")

        self._sub_reqs = sub_reqs
        for r in sub_reqs:
            self._check_args |= r._check_args

    def _perform_checks(self, handler, args, kwargs):  # pragma: no cover
        # Defined as abstract in parent, so we have to implement it!
        raise NotImplementedError


class AllRequire(CompoundRequire):
    """Succeeds only if all requirements are met.
    Tests are applied in order and the redirect and flash message are for the first to fail.
    """
    def _perform_checks(self, handler, args, kwargs):
        # pylint: disable=protected-access
        for r in self._sub_reqs:
            ok, message, catagory, target = r._perform_checks(handler, args, kwargs)
            if not ok:
                return (
                    ok,
                    self._msg if self._msg else message,
                    self._msg_cat if self._msg_cat else catagory,
                    self._redirect if self._redirect else target
                )
        return True, None, None, None

    def __and__(self, other):
        if not isinstance(other, BaseRequire):
            raise ValueError("rhs value must be another requirement")
        if isinstance(other, AllRequire):
            other_list = other._sub_reqs
        else:
            other_list = [other]
        return AllRequire(*(tuple(self._sub_reqs) + tuple(other_list)))


class AnyRequire(CompoundRequire):
    """Succeeds if any of the requirements are met.
    If none are met the redirect and lash message from the first is used.
    """
    def _perform_checks(self, handler, args, kwargs):
        # pylint: disable=protected-access
        first_fail = None
        for r in self._sub_reqs:
            result = r._perform_checks(handler, args, kwargs)
            ok, _, _, _ = result
            if ok:
                return True, None, None, None
            elif first_fail is None:
                first_fail = result
        ok, message, catagory, target = first_fail
        return (
            ok,
            self._msg if self._msg else message,
            self._msg_cat if self._msg_cat else catagory,
            self._redirect if self._redirect else target
        )

    def __or__(self, other):
        if not isinstance(other, BaseRequire):
            raise ValueError("rhs value must be another requirement")
        if isinstance(other, AnyRequire):
            other_list = other._sub_reqs
        else:
            other_list = [other]
        return AnyRequire(*(tuple(self._sub_reqs) + tuple(other_list)))
