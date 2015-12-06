API Objects
===========

The Zenpy API objects are automatically generated using the script `gen_classes.py` in the `tools` directory based on the specification found in the `specification` directory. The generated Python objects are a one to one mapping with the API, so any attribute returned by the API should be present in the Python object.

Instantiating Objects
---------------------

When creating objects, any keyword argument can be passed to the constructor and it will become an attribute of that object. For example the code:
::

    user = User(name='Jim', email='jim@jim.com')

Will create a `User` object with the name and email fields set.

Object Properties
-----------------

Many attributes are implemented as `properties`. Any attribute that holds an id is also implemented as a `property` which returns the object associated with that id. For example, the `Ticket` object has two related attributes: `assignee` and `assignee_id`. When the `assignee` attribute is accessed, Zenpy first attempts to locate the related `User` in the `User` cache and if it cannot be found will generate and execute an API call to retrieve, instantiate, cache and return the object. Accessing the `assignee_id` attribute simply returns the id.

The following attributes are also implemented as `properties`:

+--------------------+----------------------------+
| **Attribute Type** | **Returns**                |
+--------------------+----------------------------+
| dict               | object the dict represents |
+--------------------+----------------------------+
| date string        | Python datetime object     |
+--------------------+----------------------------+
| list of id's       | List of objects            |
+--------------------+----------------------------+


It is important to note that most property setters throw away all information except for the id. This is because Zendesk only expects the id, so any modifications made to the object will not be persisted automatically. For example, the following `Ticket`::

    ticket = Ticket(subject='stuffs', description='stuff stuff stuff')
    user = User(id=10, name='Jim', email='jim@jim.com')
    ticket.assignee = user

Will be serialized as::

    {
        "description": "stuff stuff stuff",
        "assignee_id": 10,
        "subject": "stuffs"
    }


Object Serialization
--------------------

Before API objects are sent to Zendesk (eg for creation/updates), they are serialized into JSON once again. This is done recursively and any nested objects will be serialized as well. One handy side effect of how this is done is it is possible to set any arbitrary attribute on an API object and it will be serialized and sent to Zendesk. For example the object::

    user = User(name='Jim', email='jim@jim.com')
    user.some_thing = 100

Will be serialized as::

    {
        "email": "jim@jim.com",
        "some_thing": 100,
        "name": "Jim"
    }



.. toctree::
    :maxdepth: 4

    api_object_docs