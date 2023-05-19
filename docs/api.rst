API
===

.. module:: flask_require

This section of the documentation details the API for flask-require.

Requirement classes
-------------------

Instances of these classes can be used either as decorators for methods of as functions
to pass the the :code:`before_request()` hook of a blueprint.

.. autoclass:: Require
   :members:
   :inherited-members:

.. autoclass:: SessionRequire
   :members:
   :inherited-members:

.. autoclass:: ValueRequire
   :members:
   :inherited-members:

.. autoclass:: ContextRequire
   :members:
   :inherited-members:

.. autoclass:: AllRequire
   :members:
   :inherited-members:

.. autoclass:: AnyRequire
   :members:
   :inherited-members:


Value test classes
------------------

These classes implement various common checks that are often applied to values in the :code:`session`
state or the global context.

.. autoclass:: Contains
   :members:
   :inherited-members:

.. autoclass:: MatchContext
   :members:
   :inherited-members:

.. autoclass:: TimeStampAge
   :members:
   :inherited-members:

Utility functions
-----------------

.. autofunction:: up

