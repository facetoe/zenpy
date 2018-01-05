[![Build Status](https://travis-ci.org/facetoe/zenpy.svg?branch=master)](https://travis-ci.org/facetoe/zenpy)
[![Coverage Status](https://coveralls.io/repos/github/facetoe/zenpy/badge.svg?branch=master&service=github)](https://coveralls.io/github/facetoe/zenpy?branch=master&service=github)

# Zenpy

Zenpy is a Python wrapper for the Zendesk, Chat and HelpCentre APIs. The goal of the project is to make it possible to write clean, fast, Pythonic code when interacting with Zendesk progmatically. The wrapper tries to keep API calls to a minimum. Wherever it makes sense objects are cached, and attributes of objects that would trigger an API call are evaluated lazily. 

Zenpy supports both Python2 and Python3.

**Note:** HelpCentre API support is in beta.

Please report bugs!

* [Quickstart](#quickstart)
* [New Features](#new-features)
    * [Pagination via Python slices](#pagination)
    * [Incremental object updates](#incremental-object-updates)
* [Examples](#examples)
    * [Creating a ticket with a different requester](#creating-a-ticket-with-a-different-requester)
    * [Commenting on a ticket](#commenting-on-a-ticket)
    * [Appending tags to a ticket](#appending-tags-to-a-ticket)
    * [Uploading an attachment](#uploading-an-attachment)
    * [Creating a ticket with a custom field set](#creating-a-ticket-with-a-custom-field-set)
    * [Updating a custom field on a ticket](#updating-a-custom-field-on-a-ticket)
    * [Applying a Macro to a ticket](#applying-a-macro-to-a-ticket)
    * [Adding a photo to a user](#adding-a-photo-to-a-user)
* [Documentation](#documentation)
* [Contributions](#contributions)

## Quickstart

```python
from zenpy import Zenpy
# Create a Zenpy instance
zenpy_client = Zenpy(**credentials)

# Create a new ticket
zenpy_client.tickets.create(Ticket(subject="Important", description="Thing"))

# Perform a simple search
for ticket in zenpy_client.search("PC LOAD LETTER", type='ticket', assignee="facetoe"):
    # No need to mess around with ids, linked objects can be accessed directly.
    print(ticket.requester)
```

## New Features
#### Pagination

Added experimental support for pagination using Python slices. Currently has a few limitations:

* Does not support negative values (no fancy slicing)
* Always pulls the first 100 objects (sometimes one extra API call than necessary)
* Does not currently support multiple accesses

Usage:
```python
ticket_generator = zenpy_client.tickets()

# Arguments to slice are [start:stop:page_size], they are all optional
tickets = ticket_generator[3950:4000:50]
print(tickets)

# Normal Python slice semantics, the following examples do what you would expect
tickets = ticket_generator[200:]
tickets = ticket_generator[:200]
tickets = ticket_generator[::]
```

#### Incremental object updates
Previously when executing code such as:

```python
ticket = zenpy_client.tickets(id=1)
ticket.status = 'pending'
zenpy_client.tickets.update(ticket)
```
Every object attribute was sent off to Zendesk. This led to subtle bugs and is inefficient. Now, only those objects that have been modified will be sent. You can see which attributes will be sent as follows:
```python
print(zenpy_object.to_dict(serialize=True))
```


## Examples

##### Creating a ticket with a different requester

```python
from zenpy.lib.api_objects import Ticket, User

zenpy_client.tickets.create(
    Ticket(description='Some description',
           requester=User(name='bob', email='bob@example.com'))
)
```

##### Commenting on a ticket

```python
from zenpy.lib.api_objects import Comment

ticket = zenpy_client.tickets(id=some_ticket_id)
ticket.comment = Comment(body="Important private comment", public=False)
zenpy_client.tickets.update(ticket)
```

##### Appending tags to a ticket

```python
from zenpy.lib.api_objects import Ticket

ticket = zenpy_client.tickets(id=some_ticket_id)
ticket.tags.extend(['onetag', 'twotag', 'threetag', 'four'])
zenpy_client.tickets.update(ticket)
```

##### Uploading an attachment

```python
from zenpy.lib.api_objects import Comment

# Upload the file (or file-like object) to Zendesk and obtain an Upload instance
upload_instance = zenpy_client.attachments.upload('/tmp/awesome_file.txt')

ticket = zenpy_client.tickets(id=some_ticket_id)
ticket.comment = Comment(body='This comment has my file attached', uploads=[upload_instance.token])
zenpy_client.tickets.update(ticket)
```

##### Creating a ticket with a custom field set

```python
from zenpy.lib.api_objects import CustomField, Ticket

ticket_audit = zenpy_client.tickets.create(Ticket(
    subject='Has custom field',
    description="Wow, such field",
    custom_fields=[CustomField(id=43528467, value=1337)]
))
```

##### Updating a custom field on a ticket

```python
from zenpy.lib.api_objects import CustomField
ticket = zenpy_client.tickets(id=some_ticket_id)
ticket.custom_fields.append(CustomField(id=43528467, value=1337))
zenpy_client.tickets.update(ticket)
```

##### Applying a Macro to a ticket

```python
# Execute the show_macro_effect() method which returns what the macro *would* do.
# The method accepts either Zenpy objects or ids. 
macro_result = zenpy_client.tickets.show_macro_effect(ticket_id_or_object, macro_id_or_object)

# Update the ticket to actually change the ticket. 
zenpy_client.tickets.update(macro_result.ticket)
```

##### Adding a photo to a user

```python
user = zenpy_client.users(id=user_id)
user.remote_photo_url = 'http://domain/example_photo.jpg'
zenpy_client.users.update(user)
```

## Documentation

Check out the [documentation](http://docs.facetoe.com.au/) for more info.

### Contributions
Contributions are very welcome. I've written an explanation of the core ideas of the wrapper in the [Contributors Guide](https://github.com/facetoe/zenpy/wiki/Contributors-Guide).
 
