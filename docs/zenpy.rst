Zenpy
=====

:class:`Zenpy` is a Python wrapper for the Zendesk API. The goal of the project
is to make it possible to write clean, fast, Pythonic code when
interacting with Zendesk progmatically. The wrapper tries to keep API
calls to a minimum. Wherever it makes sense objects are cached, and
attributes of objects that would trigger an API call are evaluated
lazily.

The wrapper supports both reading and writing from the API.

:class:`Zenpy` supports both Python2 and Python3.

:class:`Zenpy` is still in beta, so please report any bugs!

-  `Installation <#installation>`__
-  `Usage <#usage>`__
-  `Searching the API <#searching-the-api>`__
-  `Querying the API <#querying-the-api>`__
-  `Creating, Updating and Deleting API
   Objects <#creating-updating-and-deleting-api-objects>`__
-  `Bulk Operations <#bulk-operations>`__
-  `Incremental Exports <#incremental-exports>`__
-  `Caching <#caching>`__

Installation
~~~~~~~~~~~~

::

    pip install zenpy

Usage
~~~~~

First, create a :class:`Zenpy` object:

.. code:: python

    # :class:`Zenpy` accepts a token
    creds = {
        'email' : 'youremail',
        'token' : 'yourtoken'
    }

    # Or password
    creds = {
        'email' : 'youremail',
        'password' : 'yourpassword'
    }

    # Default
    :class:`Zenpy` = Zenpy('yourdomain', **creds)

    ## With debugging information
    :class:`Zenpy` = Zenpy('yourdomain', **creds, debug=True)

    ## Or with an existing requests.Session object
    :class:`Zenpy` = Zenpy('yourdomain', **creds, session=some_session)

Searching the API
-----------------

All of the search paramaters defined in the Zendesk search documentation
(https://support.zendesk.com/hc/en-us/articles/203663226) should work
fine in Zenpy. Searches are performed by passing keyword arguments to
the ``search`` endpoint. The keyword arguments line up with the Zendesk
search documentation and are mapped as follows:



    +-----------------+------------------+
    | **Keyword**     | **Operator**     |
    +-----------------+------------------+
    | keyword         | : (equality)     |
    +-----------------+------------------+
    | \*_greater_than | >                |
    +-----------------+------------------+
    | \*_less_than    | <                |
    +-----------------+------------------+
    | \*_after        | <                |
    +-----------------+------------------+
    | \*_before       | <                |
    +-----------------+------------------+
    | minus           | \- (negation)    |
    +-----------------+------------------+
    | \*_between      | > < (dates only) |
    +-----------------+------------------+

For example, the code:

.. code:: python

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    today = datetime.datetime.now()
    for ticket in zenpy.search("zenpy", created_between=[yesterday, today], type='ticket', minus='negated'):
        print ticket

Would generate the following API call:

::

    /api/v2/search.json?query=zenpy+created>2015-08-29 created<2015-08-30+type:ticket+-negated

The ordering can be controlled by passing the ``sort_by`` and/or
``sort_order`` parameters as keyword arguments, eg:

.. code:: python

    zenpy.search("some query", type='ticket', sort_by='created_at', sort_order='desc')

See the `Zendesk
docs <https://developer.zendesk.com/rest_api/docs/core/search#available-parameters>`__
for more information.

Querying the API
----------------

The :class:`Zenpy` object contains methods for accessing many top level
endpoints, and they can be called in one of two ways - no arguments
returns all results (as a generator):

.. code:: python

    for user in zenpy.users():
        print user.name

And called with an ID returns the object with that ID:

.. code:: python

    print zenpy.users(id=1159307768)

In addition to the top level endpoints there are several secondary level
endpoints that reference the level above. For example, if you wanted to
print all the comments on a ticket:

.. code:: python

    for comment in zenpy.tickets.comments(id=86):
        print comment.body

Or organizations attached to a user:

.. code:: python

    for organization in zenpy.users.organizations(id=1276936927):
        print organization.name

You could do so with these second level endpoints.

The vast majority of endpoints are supported, however I've chosen not to
implement some that seemed unlikely to be used. If there is an endpoint
that you would like to see implemented, just create a issue and I'll
look into it.

Creating, Updating and Deleting API Objects
-------------------------------------------

Many endpoints support the ``create``, ``update`` and ``delete``
operations. For example we can create a ``User`` with the following
code:

.. code:: python

    user = User(name="John Doe", email="john@doe.com")
    created_user = zenpy.users.create(user)

The ``create`` method returns the created object with it's various
attributes (such as ``id``/ ``created_at``) filled in by Zendesk.

We can update this user by modifying it's attributes and calling the
``update`` method:

.. code:: python

    created_user.role = 'agent'
    created_user.phone = '123 434 333'
    modified_user = zenpy.users.update(created_user)

Like ``create``, the ``update`` method returns the modified object.

Next, let's assign all new tickets to this user:

.. code:: python

    for new_ticket in zenpy.search(type='ticket', status='new'):
        new_ticket.assignee = modified_user
        ticket_audit = zenpy.tickets.update(new_ticket)

When updating a ticket, a ``TicketAudit``
(https://developer.zendesk.com/rest\_api/docs/core/ticket\_audits)
object is returned. This object contains the newly updated ``Ticket`` as
well as some additional information in the ``Audit`` object.

Finally, let's delete all the tickets assigned to the user:

.. code:: python

    for ticket in zenpy.search(type='ticket', assignee='John Doe'):
        zenpy.tickets.delete(ticket)

Deleting ticket returns nothing on success and raises an
``ApiException`` on failure.

Bulk Operations
---------------

Zendesk supports bulk creating, updating and deleting API objects, and
so does Zenpy. The ``create``, ``update`` and ``delete`` methods all
accept either an object, a list of objects. For
example, the code:

.. code:: python

    job_status = zenpy.tickets.create([Ticket(subject="Ticket%s" % i, description="Bulk")for i in range(0, 20)])

will create 20 tickets in one API call. When performing bulk operations,
a ``JobStatus`` object is returned
(https://developer.zendesk.com/rest\_api/docs/core/job\_statuses). The
only exception to this is bulk ``delete`` operations, which return
nothing on success and raise a ``APIException`` on failure.

It is important to note that these bulk endpoints have restrictions on
the number of objects that can be processed at one time (usually 100).
:class:`Zenpy` makes no attempt to regulate this. Most endpoints will throw an
``APIException`` if that limit is exceeded, however some simply process
the first N objects and silently discard the rest.

Incremental Exports
-------------------

Zendesk has several incremental API endpoints
(https://developer.zendesk.com/rest\_api/docs/core/incremental\_export)
to export items in bulk (up to 1000 items per request) and also to poll
the API for changes since a point in time.

Incremental endpoints accept either a datetime object or a unix
timestamp as the ``start_time`` parameter. For example, the following
code will retrieve all tickets created or modified in the last day:

.. code:: python

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    result_generator = zenpy.tickets.incremental(start_time=yesterday)
    for ticket in result_generator:
        print ticket.id

The last ``end_time`` value can be retrieved from the generator:

.. code:: python

    print result_generator.end_time

Passing this value to a new call as the ``start_time`` will return items
created or modified since that point in time.

Caching
~~~~~~~

:class:`Zenpy` maintains several caches to prevent unecessary API calls.

If we turn DEBUG on, we can see Zenpy's caching in action. The code:

.. code:: python

    print zenpy.users(id=1159307768).name
    print zenpy.users(id=1159307768).name

Outputs:

::

    DEBUG - Cache MISS: [User 1159307768]
    DEBUG - GET: https://testing23.zendesk.com/api/v2/users/1159307768.json/?include=organizations,abilities,roles,identities,groups
    DEBUG - Caching 1 Groups
    DEBUG - Caching: [User 1159307768]
    DEBUG - Caching 1 Organizations
    Face Toe
    DEBUG - Cache HIT: [User 1159307768]
    Face Toe

There a few things to note here. We can see when the user was first
requested it was not in the cache, which led to an API call. The GET
request which was generated requests the user, but it also adds an
``include`` directive to pull related objects which led to a Group and
Organization object being cached as well. This is called Sideloading by
Zendesk, and :class:`Zenpy` takes advantage of it wherever it can. We can see
that the next time the user was requested it was found in the cache and
no API call was generated.

Controlling Caching
-------------------

The :class:`Zenpy` object contains methods for adding, removing and modifying
caches. Each object type can have a different cache implementation and
settings. For example, you might use a
`TTLCache <https://pythonhosted.org/cachetools/#cachetools.TTLCache>`__
for ``Ticket`` objects with a timeout of one minute, and a
`LFUCache <https://pythonhosted.org/cachetools/#cachetools.LFUCache>`__
for ``Organization`` objects. It's even possible to change cache
implementations on the fly.

For example, to also cache SatisfactionRatings:

.. code:: python

    zenpy.add_cache(object_type='satisfaction_rating', cache_impl_name='LRUCache', maxsize=10000)


Cache method reference
----------------------

 .. cachedoc::

Default Caches
--------------

By default :class:`Zenpy` caches for following objects:

* :class:`zenpy.lib.api_objects.Comment`
* :class:`zenpy.lib.api_objects.UserField`
* :class:`zenpy.lib.api_objects.Group`
* :class:`zenpy.lib.api_objects.User`
* :class:`zenpy.lib.api_objects.OrganizationField`
* :class:`zenpy.lib.api_objects.Organization`
* :class:`zenpy.lib.api_objects.Brand`
* :class:`zenpy.lib.api_objects.TicketField`


Zenpy Endpoint Reference
------------------------

.. apidoc::
