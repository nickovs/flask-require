Flask View Requirements
-----------------------

The `Flask <https://flask.palletsprojects.com/>`_ web development framework suxpports a host of
powerful features for building web applications, but it takes a lightweight approach that leaves 
the implementation of a number of common features up to the user. One of these common cases 
providing fine-grain access control to the set of views delivered by the web application.

The :code:`flask-require` module aims to make it quicker and easier to implement rigerous access
control to views and API endpoints, while at the same time reducing the amount of typing and
"boilerplate" code needed to carry out common tasks.

Examples
--------

Suppose that when users log in, their access control rights are stored securely into the Flask
session object, and that there are some pages in your site that you want to ensure are only
accessible to users 

.. code-block:: python

    import datetime
    from flask_require import SessionRequire, Contains

    admin_only = SessionRequire(("acl_rights", "admin"), "index", "Admin rights are needed")

    ...

    @app.route("/manage_something")
    @admin_only
    def manage_things_view():
        return "This page would do some admin-only management stuff."

Installation
------------

The latest release version of :code:`flask-require` can be installed using :code:`pip` with:

.. code-block:: sh

    pip install flask-require

To install the latest development version directly from GitHub you can use:

.. code-block:: sh

    pip install https://github.com/nickovs/flask-require.git@master
