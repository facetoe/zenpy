[![Build Status](https://travis-ci.org/facetoe/zenpy.svg?branch=master)](https://travis-ci.org/facetoe/zenpy)

# Zenpy

Zenpy is a Python wrapper for the Zendesk, Chat and HelpCentre APIs. The goal of the project is to make it easy to write clean, fast, Pythonic code when interacting with Zendesk progmatically. The wrapper tries to keep API calls to a minimum. Wherever it makes sense objects are cached, and attributes of objects that would trigger an API call are evaluated lazily. 

Zenpy supports both Python2 and Python3.

**Note:** HelpCentre API support is in beta.

Please report bugs!

* [Quickstart](#quickstart)
* [Examples](#examples)
    * [Creating a ticket with a different requester](#creating-a-ticket-with-a-different-requester)
    * [Commenting on a ticket](#commenting-on-a-ticket)
    * [Adding a HTML comment to a ticket](#adding-a-html-comment-to-a-ticket)
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
for ticket in zenpy_client.search('PC LOAD LETTER', type='ticket', assignee='facetoe'):
    # No need to mess around with ids, linked objects can be accessed directly.
    print(ticket.requester.name)

    # All objects can be converted to a Python dict.
    print(ticket.to_dict())

    # Or to JSON.
    print(ticket.to_json())
```

## Examples

##### Searching open and pending tickets for a specific user and sort them by descending

```python
zenpy_client.search(type='ticket', status_less_than='closed', assignee='foo@mail.foo', sort_order='desc')
```

##### Searching only opened tickets

```python
zenpy_client.search(type='ticket', status='open')
```

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

##### Adding a HTML comment to a ticket

```python
from zenpy.lib.api_objects import Ticket, Comment

zenpy_client.tickets.create(Ticket(
    subject='Html comment example',
    comment=Comment(body='The smoke is very colorful',
                    html_body='<h2>The smoke is <i>very</i> colourful</h2>'))
)
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
 
