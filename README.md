[![Build Status](https://travis-ci.org/facetoe/zenpy.svg?branch=master)](https://travis-ci.org/facetoe/zenpy)

# Zenpy

Zenpy is a Python wrapper for the Zendesk, Chat and HelpCentre APIs. The goal of the project is to make it easy to write clean, fast, Pythonic code when interacting with Zendesk progmatically. The wrapper tries to keep API calls to a minimum. Wherever it makes sense objects are cached, and attributes of objects that would trigger an API call are evaluated lazily.

Zenpy supports both Python2 and Python3.

Please report bugs!

* [Quickstart](#quickstart)
* [Examples](#examples)
  * Ticketing
    * [Creating a ticket with a different requester](#creating-a-ticket-with-a-different-requester)
    * [Commenting on a ticket](#commenting-on-a-ticket)
    * [Adding a HTML comment to a ticket](#adding-a-html-comment-to-a-ticket)
    * [Appending tags to a ticket](#appending-tags-to-a-ticket)
    * [Uploading an attachment](#uploading-an-attachment)
    * [Creating a ticket with a custom field set](#creating-a-ticket-with-a-custom-field-set)
    * [Updating a custom field on a ticket](#updating-a-custom-field-on-a-ticket)
    * [Applying a Macro to a ticket](#applying-a-macro-to-a-ticket)
  * Users
    * [Adding a photo to a user](#adding-a-photo-to-a-user)
  * Help center
    * [List all categories from help center](#List-all-categories-from-help-center)
    * [List all help center articles](#List-all-help-center-articles)
    * [List all help center articles in a section](#List-all-help-center-articles-in-a-section)
    * [Create new category in help center](#Create-new-category-in-help-center)
    * [Create new section in help center](#Create-new-section-in-help-center)
    * [Create new article in help center](#Create-new-article-in-help-center)
  * Other
    * [Working with webhooks](#Working-with-webhooks)
    * [Pagination](#Pagination)
* [Documentation](#documentation)
* [Contributions](#contributions)

## Quickstart

```python
from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket
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

##### Exporting all tickets matching the query

By default, Search API has a limit of 1000 results in total.
Search Export API allows exporting unlimited number of results, so if you'd like to export all results, 
use this method instead:

```python
for ticket in zenpy_client.search_export(type='ticket', status='open'):
    print(ticket)
```

Read more about these limitations:

[Search results limits](https://developer.zendesk.com/api-reference/ticketing/ticket-management/search/#results-limit)

[Search Export API release notes](https://support.zendesk.com/hc/en-us/articles/4408825120538-Support-API-Announcing-the-Export-Search-Results-endpoint-)

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

##### Creating a comment attachment and then redacting it

```python
# Upload the attachment
upload_instance = zenpy_client.attachments.upload('/tmp/awesome_file.txt')
comment = Comment(body='Some comment')
# Set the comment attachment affinity to this token.
comment.uploads = upload_instance.token

# Create the ticket, with that comment with that attachment affinity.  Can just as easily be a new comment on existing ticket.
ticket = Ticket(subject='example ticket', comment=comment)
ticket_audit = zenpy_client.tickets.create(ticket)
ticket = ticket_audit.ticket

# Get the last comment we just uploaded on that ticket.
the_commentresult = zenpy_client.tickets.comments(ticket)

# Redact the comment now that we just associated it with an attachment.
the_comment = the_commentresult.values[0]  
attachment =  zenpy_client.attachments.redact(ticket, the_comment, the_comment.attachments[0].id)

# Barring no errors, the attachment is an Attachment object with the same id as was passed in!
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

##### List all categories from help center

```python
categories = zenpy_client.help_center.categories()
for category in categories:
    pass

```

##### List all help center articles

```python
articles = zenpy_client.help_center.articles(section=section)
for article in articles:
    pass
```

##### List all help center articles in a section

```python
section = zenpy_client.help_center.categories.sections(category_id=category.id)
articles = zenpy_client.help_center.sections.articles(section=section)
for article in articles:
    pass
```

##### Create new category in help center

```python
from zenpy import Zenpy
from zenpy.lib.api_objects.help_centre_objects import Category
new_category = zenpy_client.help_center.categories.create(
            Category(
                name="Category name",
                description="Category description",
                locale="en-us",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        )
print(new_category.to_dict(serialize=True))
```

##### Create new section in help center

```python
from zenpy import Zenpy
from zenpy.lib.api_objects.help_centre_objects import Section
new_section = zenpy_client.help_center.sections.create(
            Section(
                name="Section name",
                description="Section description",
                category_id=new_category.id,
                locale="en-us",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        )
print(new_section.to_dict(serialize=True))
```

##### Create new article in help center

```python
from zenpy import Zenpy
from zenpy.lib.api_objects.help_centre_objects import Article
new_article = zenpy_client.help_center.articles.create(
                    section=new_section.id,
                    article=Article(
                        name="Article Name",
                        body="<p>Article html content body</p>",
                        locale="en-us",
                        title="Article title",
                        section_id=new_section.id,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    ),
                )
print(new_article.to_dict(serialize=True))
```

##### Working with webhooks

###### Show a webhook
```python
webhook = zenpy_client.webhooks(id=WEBHOOK_ID) 
```

###### List webhooks
```python
# Just list all the webhooks
for webhook in zenpy_client.webhooks.list():
    pass # Do something with it

# Filter the webhooks by a string in the name
for webhook in zenpy_client.webhooks.list(filter='some string'):
    pass # Do something with it

# Using sorting and pagination according to https://developer.zendesk.com/api-reference/event-connectors/webhooks/webhooks/#list-webhooks
zenpy_client.webhooks.list(sort='name')
zenpy_client.webhooks.list(page_before=X, page_size=Y)
zenpy_client.webhooks.list(page_after=N, page_size=Y)
```

###### Creating a webhook that uses basic authentication
```python
from zenpy.lib.api_objects import Webhook

new_webhook = Webhook(
    authentication={
        "add_position": "header",
        "data": {
            "password": "hello_123",
            "username": "john_smith"
        },
        "type": "basic_auth"
    },
    endpoint="https://example.com/status/200",
    http_method="GET",
    name="Example Webhook",
    description="Webhook description",
    request_format="json",
    status="active",
    subscriptions=["conditional_ticket_events"],
) 
zenpy_client.webhooks.create(new_webhook)
```

###### Creating a webhook that uses no authentication
```python
new_webhook = Webhook(
    endpoint="https://example.com/status/200",
    http_method="GET",
    name="Example Webhook",
    description="Webhook description",
    request_format="json",
    status="active",
    subscriptions=["conditional_ticket_events"],
) 
zenpy_client.webhooks.create(new_webhook)
```

###### Creating a webhook that uses bearer token authentication
```python
new_webhook = Webhook(
    authentication={
        "add_position": "header",
        "data": {
            "token": "{{token}}"
        },
        "type": "bearer_token"
    },
    # other fields
) 
zenpy_client.webhooks.create(new_webhook)
```

###### Updating a webhook
```python
from zenpy.lib.api_objects import Webhook

webhook = zenpy_client.webhooks(id=WEBHOOK_ID) 

# Note: We need a brand new object because of API specific requirements for 'update'
# https://developer.zendesk.com/api-reference/event-connectors/webhooks/webhooks/#update-webhook

new_webhook = Webhook(
                    name="New name",
                    request_format="json",
                    http_method="GET",
                    endpoint="https://example.com/status/200",
                    status="active",
                    authentication={
                      "add_position": "header",
                      "data": {
                          "password": "hello_123",     # As we can't get it back we need to pass it again from scratch
                          "username": "john_smith"
                      },
                      "type": "basic_auth"
                  },
)
response = zenpy_client.webhooks.update(webhook.id, new_webhook)
```

###### Partially updating (patching) a webhook
```python
webhook = zenpy_client.webhooks(id=WEBHOOK_ID)
webhook.name = 'A new name'
response = zenpy_client.webhooks.patch(webhook)
```

###### Cloning a webhook
```python
from zenpy.lib.api_objects import Webhook

an_existing_webhook = zenpy_client.webhooks(id=WEBHOOK_ID) 
new_webhook = zenpy_client.webhooks.clone(an_existing_webhook)

# Or just
new_webhook = zenpy_client.webhooks.clone(WEBHOOK_ID)
```

###### Working with secrets
```python

secret = zenpy_client.webhooks.show_secret(webhook)
print(secret.secret)

secret = zenpy_client.webhooks.reset_secret(webhook)
print(secret.secret)
```

###### Testing webhooks
```python

# Testing an existing webhook "as is""
response = zenpy_client.webhooks.test(webhook)

# Testing an existing webhook with modifications 
response = zenpy_client.webhooks.test(
                    webhook, 
                    request=dict(
                      endpoint='https://example.org/'
                    )
)

# Sending a test request without creating a webhook
response = zenpy_client.webhooks.test(
                    request=dict(
                        endpoint="https://example.org",
                        request_format="json",
                        http_method="GET",
                    )
                )
```

###### Getting a webhook invocations

[API documentation](https://developer.zendesk.com/api-reference/webhooks/webhooks-api/webhooks/#list-webhook-invocations)

```python
wh_filters = {
    'filter[from_ts]': '2023-12-04T12:00:00Z',
    'filter[to_ts]': '2023-12-04T16:00:00Z',
    'filter[status]': 'success',
}

for invocations in zenpy.webhooks.invocations(webhook_id, **wh_filters):
    pass

```

##### Pagination

Please refer to the [official documentation](https://developer.zendesk.com/api-reference/introduction/pagination/) to get details. Also check this article: [Which endpoints are supported?](https://support.zendesk.com/hc/en-us/articles/4408846180634#h_01FF626TG8VD0W4JP9DBBSXESK)

```python
# An old style offset pagination, not recommended. Since August 15, 2023, is limited to 100 pages.
fields = zenpy_client.ticket_fields()
# Or
fields = zenpy_client.ticket_fields(cursor_pagination=False)

# A new cursor offset pagination
fields = zenpy_client.ticket_fields(cursor_pagination=True) # is equal to 100 results per page
# Or
fields = zenpy_client.ticket_fields(cursor_pagination=50) # 50 results per page

```

## Documentation

Check out the [documentation](http://docs.facetoe.com.au/) for more info.

### Contributions
Contributions are very welcome. I've written an explanation of the core ideas of the wrapper in the [Contributors Guide](https://github.com/facetoe/zenpy/wiki/Contributors-Guide).
