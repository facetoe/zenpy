[![Build Status](https://travis-ci.org/facetoe/zenpy.svg?branch=master)](https://travis-ci.org/facetoe/zenpy)

# Zenpy

Zenpy is a Python wrapper for the Zendesk API. The goal of the project is to make it possible to write clean, fast, Pythonic code when interacting with Zendesk progmatically. The wrapper tries to keep API calls to a minimum. Wherever it makes sense objects are cached, and attributes of objects that would trigger an API call are evaluated lazily. 

The wrapper supports both reading and writing from the API.

Zenpy supports both Python2 and Python3. 

Please report bugs!

Note: I'm currently performing a fairly major refactor of Zenpy. If you have issues with the master branch, please submit an issue and try using the latest stable version. 

* [Quickstart](#quickstart)
* [Examples](#examples)
    * [Creating a ticket with a different requester](#creating-a-ticket-with-a-different-requester)
    * [Commenting on a ticket](#commenting-on-a-ticket)
    * [Uploading an attachment](#uploading-an-attachment)
    * [Creating a ticket with a custom field set](#creating-a-ticket-with-a-custom-field-set)
    * [Updating a custom field on a ticket](#updating-a-custom-field-on-a-ticket)
    * [Applying a Macro to a ticket](#applying-a-macro-to-a-ticket)
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
for ticket in zenpy_client.search("party", type='ticket', assignee="face"):
    print(ticket)
```

## Examples

##### Creating a ticket with a different requester

```python
from zenpy.lib.api_objects import Ticket, User

zenpy_client.tickets.create(
    Ticket(
        description='Some description',
        requester=User(name='bob', email='bob@example.com')
    )
)
```

##### Commenting on a ticket

```python
from zenpy.lib.api_objects import Comment

ticket = zenpy_client.tickets(id=some_ticket_id)
ticket.comment = Comment(body="Important private comment", public=False)
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

## Documentation

Check out the [documentation](http://docs.facetoe.com.au/) for more info.

### Contributions
Contributions are very welcome. 


