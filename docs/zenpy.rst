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

    # Zenpy accepts an API token
    creds = {
        'email' : 'youremail',
        'token' : 'yourtoken',
        'subdomain': 'yoursubdomain'
    }

    # An OAuth token
    creds = {
      "subdomain": "yoursubdomain",
      "oauth_token": "youroathtoken"
    }

    # Or a password
    creds = {
        'email' : 'youremail',
        'password' : 'yourpassword',
        'subdomain': 'yoursubdomain'
    }

    # Import the Zenpy Class
    from zenpy import Zenpy

    # Default
    zenpy_client = Zenpy(**creds)

    # Alternatively you can provide your own requests.Session object
    zenpy_client = Zenpy(**creds, session=some_session)

    # If you are providing your own HTTPAdapter object, Zenpy provides defaults via the
    # Zenpy.http_adapter_kwargs() method. You can choose to use these defaults like so:
    session = requests.Session()
    session.mount('https://', MyAdapter(**Zenpy.http_adapter_kwargs()))
    zenpy_client = Zenpy(**creds, session=some_session)

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
    | \*_greater_than | > (numeric|type) |
    +-----------------+------------------+
    | \*_less_than    | < (numeric|type) |
    +-----------------+------------------+
    | \*_after        | > (time|date)    |
    +-----------------+------------------+
    | \*_before       | < (time|date)    |
    +-----------------+------------------+
    | minus           | \- (negation)    |
    +-----------------+------------------+
    | \*_between      | > < (dates only) |
    +-----------------+------------------+

For example, the code:

.. code:: python

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    today = datetime.datetime.now()
    for ticket in zenpy_client.search("zenpy", created_between=[yesterday, today], type='ticket', minus='negated'):
        print ticket

Would generate the following API call:

::

    /api/v2/search.json?query=zenpy+created>2015-08-29 created<2015-08-30+type:ticket+-negated

The ordering can be controlled by passing the ``sort_by`` and/or
``sort_order`` parameters as keyword arguments, eg:

.. code:: python

    zenpy_client.search("some query", type='ticket', sort_by='created_at', sort_order='desc')

See the `Zendesk
docs <https://developer.zendesk.com/rest_api/docs/core/search#available-parameters>`__
for more information.

Querying the API
----------------

The :class:`Zenpy` object contains methods for accessing many top level
endpoints, and they can be called in one of two ways - no arguments
returns all results (as a generator):

.. code:: python

    for user in zenpy_client.users():
        print user.name

And called with an ID returns the object with that ID:

.. code:: python

    print zenpy_client.users(id=1159307768)

You can also filter by passing in ``permission_set`` or ``role``.

In addition to the top level endpoints there are several secondary level
endpoints that reference the level above. For example, if you wanted to
print all the comments on a ticket:

.. code:: python

    for comment in zenpy_client.tickets.comments(ticket=86):
        print comment.body

Or organizations attached to a user:

.. code:: python

    for organization in zenpy_client.users.organizations(user=1276936927):
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

    from zenpy.lib.api_objects import User

    user = User(name="John Doe", email="john@doe.com")
    created_user = zenpy_client.users.create(user)

The ``create`` method returns the created object with it's various
attributes (such as ``id``/ ``created_at``) filled in by Zendesk.

We can update this user by modifying it's attributes and calling the
``update`` method:

.. code:: python

    created_user.role = 'agent'
    created_user.phone = '123 434 333'
    modified_user = zenpy_client.users.update(created_user)

Like ``create``, the ``update`` method returns the modified object.

Next, let's assign all new tickets to this user:

.. code:: python

    for new_ticket in zenpy_client.search(type='ticket', status='new'):
        new_ticket.assignee = modified_user
        ticket_audit = zenpy_client.tickets.update(new_ticket)

When updating a ticket, a ``TicketAudit``
(https://developer.zendesk.com/rest\_api/docs/core/ticket\_audits)
object is returned. This object contains the newly updated ``Ticket`` as
well as some additional information in the ``Audit`` object.

Finally, let's delete all the tickets assigned to the user:

.. code:: python

    for ticket in zenpy_client.search(type='ticket', assignee='John Doe'):
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

    job_status = zenpy_client.tickets.create(
        [Ticket(subject="Ticket%s" % i, description="Bulk") for i in range(0, 20)]
    )

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
    result_generator = zenpy_client.tickets.incremental(start_time=yesterday)
    for ticket in result_generator:
        print ticket.id

The last ``end_time`` value can be retrieved from the generator:

.. code:: python

    print result_generator.end_time

Passing this value to a new call as the ``start_time`` will return items
created or modified since that point in time.


Pagination
----------

Pagination in Zenpy is supported via Python slices. The current implementation has a few limitations:

* Does not support negative values (no fancy slicing)
* Always pulls the first 100 objects (sometimes one extra API call than necessary)
* Does not support multiple accesses of the same slice

Example Usage:

.. code:: python

    ticket_generator = zenpy_client.tickets()

    # Arguments to slice are [start:stop:page_size], they are all optional
    tickets = ticket_generator[3950:4000:50]
    print(tickets)

    # The following examples do what you would expect
    tickets = ticket_generator[240:]
    tickets = ticket_generator[:207]
    tickets = ticket_generator[::]


Cursor Based Generators
-----------------------

Zendesk uses cursor based pagination for the TicketAudit endpoint. The use of a cursor allows you to change
the direction in which you consume objects. This is supported in Zenpy via the reversed() Python method:

.. code:: python

    audit_generator = zenpy_client.tickets.audits()
    # You can retrieve the cursor values from the generator.
    print(audit_generator.after_cursor, audit_generator.before_cursor)

    # Iterate over the last 1000 audits.
    for audit in audit_generator:
        print(audit)

    # You can pass an explicit cursor value to consume audits create after that point.
    for audit in zenpy_client.tickets.audits(cursor='fDE1MTc2MjkwNTQuMHx8'):
        print(audit)

    # Reversing the generator reverses the direction in which you consume objects. The
    # following grabs objects from just before the cursor value until the beginning of time.
    for audit in reversed(zenpy_client.tickets.audits(cursor='fDE1MTc2MjkwNTQuMHx8')):
        print(audit)


Rate Limiting
-------------

Zendesk imposes rate limiting (https://developer.zendesk.com/rest_api/docs/core/introduction#rate-limits). By default Zenpy will detect this and wait the required period before trying again, however for some use cases this is not desirable. Zenpy offers two additional configuration options to control rate limiting:

1.  `proactive_ratelimit`

    If you wish to avoid ever hitting the rate limit you can set the `proactive_ratelimit` parameter when instantiating Zenpy:

    .. code:: python

        zenpy_client = Zenpy(proactive_ratelimit_request_interval=20, **creds)

2. `proactive_ratelimit_request_interval`

    When utilizing the `proactive_ratelimit` feature, you can also specify how long to wait when you are over your `proactive_ratelimit`.

3.  `ratelimit_budget`

    If you have a maximum amount of time you are willing to wait for rate limiting, you can set the `ratelimit_budget` parameter. This budget is decremented for every second spent being rate limited, and when the budget is spent throws a RatelimitBudgetExceeded exception. For example, if you wish to wait no more than 60 seconds:

    .. code:: python

        zenpy_client = Zenpy(ratelimit_budget=60, **creds)

Side-Loading
------------
Zendesk supports "side-loading" objects to reduce the number of API calls necessary to retrieve what you are after - https://developer.zendesk.com/rest_api/docs/core/side_loading. Zenpy currently only minimally supports this feature, however I plan to add proper support for it soon. If this is something you really want raise an issue and I will get to it sooner. To take advantage of this feature for those endpoints that support it, simple pass an "include" kwarg with the objects you would like to load, eg:

.. code:: python

    for ticket in zenpy_client.tickets(include=['users']):
        print(ticket.submitter)

The code above will not need to generate an additional API call to retrieve the submitter as it was returned and cached along with the ticket.

Caching
~~~~~~~

:class:`Zenpy` support caching objects to prevent API calls, and each Zenpy instance has it's own set of caches.

If we turn logging on, we can see Zenpy's caching in action. The code:

.. code:: python

    me = zenpy_client.users.me()
    user = zenpy_client.users(id=me.id)
    user = zenpy_client.users(id=me.id)

Outputs:

::

    DEBUG - GET: https://d3v-zenpydev.zendesk.com/api/v2/users/me.json - {'timeout': 60.0}
    DEBUG - Caching: [User(id=116514121092)]
    DEBUG - Cache HIT: [User 116514121092]
    DEBUG - Cache HIT: [User 116514121092]

Here we see that only one API call is generated, as the user already existed in the cache after the first call.

This feature is especially useful when combined with "sideloading" (https://developer.zendesk.com/rest_api/docs/core/side_loading). As an example, the following code:

.. code:: python

    ticket = zenpy_client.tickets(id=6569, include='users')
    print(ticket.requester.name)

Outputs:

::

    DEBUG - Cache MISS: [Ticket 6569]
    DEBUG - GET: https://d3v-zenpydev.zendesk.com/api/v2/tickets/6569.json?include=users - {'timeout': 60.0}
    DEBUG - Caching: [Ticket(id=6569)]
    DEBUG - Caching: [User(id=116514121092)]
    DEBUG - Cache HIT: [User 116514121092]

We can see that because we "sideloaded" users, an extra API call was not generated when we attempted to access the requester attribute.

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

    zenpy_client.add_cache(object_type='satisfaction_rating', cache_impl_name='LRUCache', maxsize=10000)


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
* :class:`zenpy.lib.api_objects.Organization`
* :class:`zenpy.lib.api_objects.Brand`


Zenpy Endpoint Reference
~~~~~~~~~~~~~~~~~~~~~~~~

.. apidoc::
