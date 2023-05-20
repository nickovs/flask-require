:code:`flask_require` Tutorial
==================================

Simplifying common patterns
---------------------------

When building web applications there are many patterns that show up repeatedly. One of more common patterns is the need to perform some sort of check before a request is processed and to redirect the user if the check fails. We might need to check if a user is logged in and that the session has not expired, and if not then redirect the user to the authentication page. We might need to check that the object ID in some request parameter is valid; if so, is the current user authorised to access that object? Some cases are simple: if the user clicked Cancel on a form then send them back to the previous page rather than processing the form contents. In other case we might want not only perform a check but also start to process parts of the request. :code:`flask-require` can help with all of these case.


View requirements
-----------------

The core class provided by :code:`flask-require` is the :class:`.Require` class. This class
encapsulates a check to be carried out, a redirection to be triggered if the check fails and
optionally a message to be presented to the user using Flask's :external:py:func:`flash() <flask.flash>` mechanism.

By way of an example, let's say that you have a number of views that you want to only be accessible
on Wednesdays. This can be implemented thus:

.. code-block:: python

    from datetime import date
    from flask_require import Require

    wednesday_only = Require(
        lambda: date.today().weekday() == 2,
        "index",
        "Sorry, that page is only visible on Wednesdays"
    )

    ...

    @app.route("/hebdomadal_view")
    @wednesday_only
    def my_weekly_view():
        return "Today was originally known as 'Wōdnesdæg', the day of Odin."


In this example we create the :code:`wednesday_only` decorator with three components. The first is
a function (in this case an anonymous lambda, but it could be any function), that returns :code:`True`
if the requirement is met and :code:`False` otherwise. The second is the Flask endpoint to which the
user should be redirected if the requirement is not met. Finally, there is a message that will
be posted using Flask's :external:py:func:`flash() <flask.flash>` function so that it can be displayed
to the user.

Of course wanting a page that only displays on Wednesdays is not hugely useful. More commonly
you might want to look at some of the request information. Consider the case where you present
various forms to the user; as well as having a default **Submit** button they might also have a
**Cancel** button. When the user presses the **Cancel** button you don't want to carry out the normal
form processing but instead want to go back to some other page. If all the forms have their
**Cancel** button named :code:`cancel` then we can use:

.. code-block:: python

    from flask import request
    from flask_require import Require
    ...

    not_cancelled = Require(lambda: "cancel" not in request.values, "index")

Now any view that you decorate with :code:`@not_cancelled` will redirect to the index view if the cancel
button was pressed. That, however, might not be what you want; sending the user back to the top
index whenever any form gets cancelled is probably not a great user experience. Fortunately the
:code:`redirect_endpoint` argument does not need to be static value; you can also provide a callable
function which will return the URL to which the user will be redirected. This function can look
at the :external:py:attr:`flask.request` information, or any other state or session information, to
determine where to send the user.

.. note::
    If you use a callable to generate the redirection target it must return a URL. If you just provide
    string then it will be interpreted as a full URL if it starts with :code:`http:` or :code:`https:`,
    as a path on the local server (if it starts with a :code:`/`) or as a Flask endpoint name to be passed
    to Flask's :external:py:func:`url_for() <flask.url_for>` function if neither of the other paterns match.


Traversing the view tree
------------------------

If you have built your application with a hierarchical set of views, perhaps using Flask's
"blueprints", then one very common target for redirection is to conceptually go *up* the
hierachy. This is a sufficiently common scenario that :code:`flask_require` provides a utility
function :func:`.up` that returns the URL path of the current view with the last segment removed,
so if your form was at the path :code:`/foo/bar/form` the :func:`.up()` will return :code:`/foo/bar/`.
Using this we can make a more generic decroator for handling cancelled forms:

.. code-block:: python

    from flask import request
    from flask_require import Require, up
    ...

    not_cancelled = Require(lambda: "cancel" not in request.values, up)

This can be used to decorate any form view, anywhere in your app, and if a button called :code:`cancel`
is submitted then it will redirect to the next page up the path.


Checking parameters and session state
-------------------------------------

A great many of the tests that we want to apply before granting access to a view come down
to checking if some attributes of the session or the request context or some parameters in
the request meet some conditions. We may want to validate that the user has a properly logged in
session, that some part of the request is properly formed and refers to an entry in a database,
or that the record referred to is accessible by the current user. Many of these cases can
be implemented directly using the generic :class:`.Require` class, but :code:`flask_require`
also provides some handy subclasses that make handling these cases simpler.


Checking session state
~~~~~~~~~~~~~~~~~~~~~~

Flask provides a convenient way to securely store and retrieve session information by
means of the :py:attr:`flask.session` proxy object, which provides a key/value store
that persists across calls from the same client session. It is common to store information
about a logged in user in the session object and it is just as common to then want to use
that session state when deciding if a user should have access to certain views. While this
can be done using the base :class:`.Require` class, the :class:`.SessionRequire` class
makes it even easier to create decorators that check if values in the session state meet
required conditions.

For each key to be checked, the :class:`.SessionRequire` supports several different modes
of checking:

* If just a single key name is passed, it will test if an key of that name is present in
  the session and if the associated value is not empty.

* If a tuple of a key name and a non-list value is passed, it will test if a key
  of that name is present in the session and that the associated value for the key
  is equal to the value given.

* If a tuple of a key name and a list is passed, it will check that the key is
  present and then test if the associated value equals any of the values in the list.

* If a tuple of a key name and a callable is passed then it will check for the presence
  of the key and then call the callable passing the associated value as its single argument;
  the callable should return :code:`True` if the value is acceptable.

When a :class:`.SessionRequire` class is instantated it can be given any one of these tests,
or it can be given a list of any of these tests, in which case all tests must pass.

Here are a few example cases:

.. code-block:: python

    # A decorator to check if logged_in_user is set in the session
    logged_in = SessionRequire("logged_in_user", "login_page", "You must be logged in")
    # A decorator to check if the login_user_group is has the value "admin"
    is_admin = SessionRequire(("login_user_group", "admin"), up, "You must be an admin to access this")
    # A decorator to check if the user has a bushy tail that provides shade
    is_sciuridae = SessionRequite(
        ("user_species", ["squirrel", "chipmunk"]),
        up, "Your tail is not bushy enough to see this page")
    # A decorator to ensure the user's session has not timed out
    not_timed_out = SessionRequite(
        ("login_time", lambda t: t + timeout_period > time.time()),
        "login_page", "Your session has timed out.")


Checking the request context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As well as providing persistent state storage between requests using the
:py:attr:`flask.session` object, Flask also has a convenient way to pass state
between stages of processing of a single request in the form of the request
context object :py:attr:`flask.g`. To support view requirements based on the
values in this request context, we have the :class:`.ContextRequire` class.
This class behaves exactly like :class:`.SessionRequire` except that the keys
are looked up in the request context rather than the session context.

.. note::
    A new, empty, request context is created when a request comes in and it
    is destroyed when the request processing finishes. For :class:`.ContextRequire`
    to be useful some code needs to have run before the decorator is executed.
    Fortunately the test functions called by :class:`.Require` and its subclasses
    can have side effects that modify the request context :py:attr:`flask.g`.
    This allows you to write tests that put data into :py:attr:`flask.g` and
    then have later decorators that check values in that context.



Checking query parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

When a form is posted to a web site the fields in the form are packed up and sent to the
server. In the case of a :code:`GET` form the parameters are packed onto the end of the URL
while for a :code:`POST` form the parameters are send in the body of the HTTP request. In
either case it is common to have a set of validation checks on the values before the code
can properly process the request. The :class:`.ValueRequire` class behaves like
:class:`.SessionRequire` and :class:`.ContextRequire`, except that it checks values in
the posted query rather then the session context or the request context.

Here are a few example cases:

.. code-block:: python

    # A decorator to check if the username value was given
    has_username = ValueRequire("username", up, "A user name must be provided")
    # A decorator to check if the user typed "Confirm" in a confirmation field
    confirmed = ValueRequire(("confirm_box", "Confirm"), up, "Please type 'Confirm' in the box")
    # A decorator to ensure that

    def _check_valid_product(product_id):
        # Look up the product ID and return True if it is valid ...

    valid_product_field = ValueRequire(_check_valid_product, up, "Invalid Product", "error")



Checking path parameters
~~~~~~~~~~~~~~~~~~~~~~~~

While the values posted by forms are a good way to get parameters from user input, it is also
common to have parameters embedded in page links. In this case the parameters form some part
of the URL path. Flask supports routing rules that contain variable sections. The variables are
extacted during the route matching and are then passed to your view function.

Althought Flask provides some simple type checking, it is often necessary to check if the extracted
value is not just syntactically correct but also a valid value. For example, if we want to view
a product that is identified by a integer product ID we don't just need to know that the ID
extracted from the URL is an integer but that it represents a valid product. When you write a
handler for a route that contains variables, the variable parts are passed as parameters to the
handler, mapped to the argument names in the handler. If you want to use a :class:`.Require` to
perform a test that checks any of these variables then you can simply provide a check function
also take arguments of the same name. In the example above, the code might look like this:

.. code-block:: python

    def _check_valid_product(product_id):
        # Look up the product ID and return True if it is valid ...

    valid_product_path = Require(_check_valid_product, "index", "Unknown product")

    ...

    @app.route('/product/<int:product_id>/view')
    @valid_product_path
    def view_product(product_id):
        # Display product details
        ...


.. note::
    A Flask handler for a route that contains variables must use all of the variables that are
    extracted from the path; a checking function does not. If your route matches multiple
    variable parts but you don't need to check all of these you only need to have arguments for
    the variable names that matter to the check function.

Convenience functions for value checks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The value checking mechanisms provided by `.ValueRequire`, :class:`.SessionRequire` and
:class:`.ContextRequire` allow for any callable to be provided to perform the check.
While it's easy enough to roll your own function, :code:`flask-require` provides a few
common ones for you that can help make your code more readable.

Instances of the :class:`.Contains` class are callable and will check if the value that
you are checking *contains* the value provided to the constructor. In one of the examples
above we wrote a decorator that checked if the group associated with a user was "admin"
before granting access. In practice a user might well belong to multiple groups and have
multiple rights. In this case a better way to perform this check would be to keep a list
of groups in the session context and then write

.. code-block:: python

    # A decorator to check if "admin" is included in user_group_list
    is_admin = SessionRequire(("user_group_list", Contains("admin")), up, "You must be an admin to access this")

Instances of the :class:`.TimeStampAge` offer and easy way to check is some timestamp
value is not more than some distance back in time. The previous example for this could be
made more reable as follows:

.. code-block:: python

    # A decorator to ensure the user's session has not timed out
    not_timed_out = SessionRequite(TimeStampAge("24h"), "login_page", "Your session has timed out.")


Combining requirements
----------------------

Instances of :class:`.Require` can be combined by using instances of
:class:`.AnyRequire` and :class:`.AllRequire` to create a new requirement that
passes either if any of the provided requirements are met or only if all of them are
met. When you create these classes you can optionally pass new redirect targets, new
flash messages or both; if you don't then the target from the first requirement to
fail will be used.

.. note::
    In the case of :class:`.AllRequire`, if any of the
    requirements fail then the requirements listed later during contruction won't be
    executed.

As a convenience the boolean :code:`|` (or) and :code:`&` (and) operators can be used
to combine requirements if you don't want to provide a new target or message. Note that
although these are acting as boolean rather than bitwise operators, you need to use the
single :code:`|` and :code:`&` rather than the double  :code:`||` and :code:`&&`, since
those operators can not be overridden by a class.

.. code-block:: python

    # A decorator to test if the user ID in the path is valid; save the user data if it is
    def _user_check(user_id):
        g.user_data = database_lookup_user(user_id)
        return g.user_data is not None

    valid_user = Require(_user_check, up, "Invalid user ID")

    # A decorator to check is the looked up user is the same as the user in the session
    same_user = SessionRequire(
        ("user_id", lambda u: u == g.user_data.user_id),
        up, "You can not manage other users"
    )

    # A decorator to check if "admin" is included in user_group_list
    is_admin = SessionRequire(("user_group_list", Contains("admin")), up, "You must be an admin to access this")

    # A combined decorator that tests if the caller is allowed to manage a specific user_id
    can_manager_user = valid_user & (same_user | is_admin)

    ...

    @app.route('/users/<int:user_id>/edit')
    @can_manager_user
    def edit_user(user_id):
        # If we get here then the user_id is a valid user, the user details are
        # already cached in g.user_data and the user is either editting themselves
        # or they are an admin.
        ...


Requirements with side effects
------------------------------

Many of the use cases for :code:`flask-require` involve making decorators that have side effects.
For instance, in the example above, the :code:`valid_user` not only ensures that the :code:`user_id`
value is valid but it saves the user information into the request context so that later code does
not need to look up the same data again.

There are many places where :code:`flask-require` can take a user-defined function, and any of these
functions might have side effects. If some of these functions also want to rely on the side effects
of other functions then it's important to understand the order in which they get called, and sometimes
if they are going to get called at all.

The short answer to the question of in what order are they called is: "the obvious order". Python
generaly progresses from top to bottom through the lines, from left to right within a line and the
start to end in lists, and so does :code:`flask-require`. If you have multiple requirement decorators
on a single function then they will be executed top to bottom. This means that if one decorator is
going to rely on the side effect of another then it needs to come later, just like in a regualr Python
program. It also means that if an earlier requirement fails then later requirements won't be called;
if those later ones could have side effects then they won't be triggered. In general this is fine if
the side effect only modifies the request context but if you tried to modify the session state then
this might cause unexpected behaviour.

The other place where you might have multiple requirement test functions with side effects is when
you combine a set of requirements with boolean operators or directly construct :class:`.AnyRequire`
or :class:`.AllRequire` instances. The case for :class:`.AllRequire` is much the same as with
having multiple decorators: processing proceeds from the start of the list to the end of the list
(or from left to right, if the :code:`&` operator was used) and if an earlier test fails then the
later tests will not be tried. With :class:`.AnyRequire` (or the :code:`|` operator) it is the
opposite: it keeps going as long as the tests fail but if any test passes then later tests will
not be tried. Note that if you combine requirements with both :code:`&` and :code:`|` then they
are grouped with the normal operator precidence: :code:`&` binds more tightly than :code:`|`. This
means that if you have requirements :code:`a`, :code:`b` and :code:`c` and you build the compound
requirement :code:`a & b | c` then should the test for :code:`a` fail, the test for :code:`b` will
not be executed but the test for :code:`c` will be.

The best way to avoid confusion when write tests with side effects is to (a) only modify the
request context or other request-specific state and (b) only have leave side effects if your
test passes. If you stick to those rules then in most cases you will be safe.
