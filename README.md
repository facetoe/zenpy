# Zenpy
Python wrapper for the Zendesk API

## About
Zenpy is a Python wrapper for the Zendesk API. The goal of the project is to make it possible to write clean, fast, Pythonic code when interacting with Zendesk progmatically. The wrapper tries to keep API calls to a minimum. Wherever it makes sense objects are cached, and attributes of objects that would trigger an API call are evaluated lazily. 

The wrapper supports both reading and writing from the API.


* [Usage](#usage)
*  [Searching the API](#searching-the-api)
* [Querying the API](#querying-the-api)
* [Creating, Updating and Deleting API Objects](#creating-updating-and-deleting-api-objects)
* [Bulk Operations](#bulk-operations)
* [Caching](#caching)

# Usage
First, create a Zenpy object:
```python
zenpy = Zenpy('yourdomain', 'youremail', 'yourtoken')
```

### Searching the API

All of the search paramaters defined in the Zendesk search documentation (https://support.zendesk.com/hc/en-us/articles/203663226) should work fine in Zenpy. Searches are performed by passing keyword arguments to the `search` endpoint. The keyword arguments line up with the Zendesk search documentation and are mapped as follows:
```
		keyword			= : (equality)
		*_greater_than 	= >
		*_less_than 	= <
		*_after 		= >
		*_before 		= <
		minus			= - (negation)
		*_between		= > < (only works with dates)
		query           = literal string, eg "product"
```

For example, the code:

```python
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
today = datetime.datetime.now()
for ticket in zenpy.search(query="zenpy", created_between=[yesterday, today], type='ticket', minus='negated'):
	print ticket
```

Would generate the following API call:

```
/api/v2/search.json?query=zenpy+created>2015-08-29 created<2015-08-30+type:ticket+-negated
```


### Querying the API
The Zenpy object contains methods for accessing the following top level API endpoints: `search`, `groups`, `users`, `organizations` and `tickets`. The `groups`, `users`, `organizations` and `tickets` top level endpoints are pretty simple, and they can be called in one of two ways - no arguments returns all results (as a generator):

```python
for user in zenpy.users():
	print user.name
```

And called with an ID returns the object with that ID:

```python
print zenpy.users(id=1159307768)
```

In addition to the top level endpoints there are several secondary level endpoints that reference the level above. For example, if you wanted to print all the comments on a ticket:

```python
for comment in zenpy.tickets.comments(id=86):
	print comment.body
```

Or organizations attached to a user:

```python
for organization in zenpy.users.organizations(id=1276936927):
	print organization.name
```

You could do so with these second level endpoints. 

### Creating, Updating and Deleting API Objects

Many endpoints support the `create`, `update` and `delete` operations. For example we can create a `User` with the following code:

```python
user = User(name="John Doe", email="john@doe.com")
created_user = zenpy.users.create(user)
```

The `create` method returns the created object with it's various attributes (such as `id`/ `created_at`) filled in by Zendesk.

We can update this user by modifying it's attributes and calling the `update` method:

```python
created_user.role = 'agent'
created_user.phone = '123 434 333'
modified_user = zenpy.users.update(created_user)
```

Like `create`, the `update` method returns the modified object. 

Next, let's assign all new tickets to this user:

```python
for new_ticket in zenpy.search(type='ticket', status='new'):
	new_ticket.assignee_id = modified_user.id
	ticket_audit = zenpy.tickets.update(new_ticket)
```

When updating a ticket, a `TicketAudit` (https://developer.zendesk.com/rest_api/docs/core/ticket_audits) object is returned. This object contains the newly updated `Ticket` as well as some additional information in the `Audit` object. 

Finally, let's delete all the tickets assigned to the user:

```python
for ticket in zenpy.search(type='ticket', assignee='John Doe'):
	zenpy.tickets.delete(ticket)
```

Deleting  ticket returns nothing on success and raises an `Exception` on failure. 

### Bulk Operations

Zendesk supports bulk creating, updating and deleting API objects, and so does Zenpy. The `create`, `update` and `delete` methods all accept either an object, a list of objects or a `ResultGenerator`. For example, the code:

```python
job_status = zenpy.tickets.create([Ticket(subject="Ticket%s" % i, description="Bulk")for i in range(0, 20)])
```
will create 20 tickets in one API call. When performing bulk operations, a `JobStatus` object is returned (https://developer.zendesk.com/rest_api/docs/core/job_statuses). The only exception to this is bulk `delete` operations, which return nothing on success and raise a `APIException` on failure.

It is important to note that these bulk endpoints have restrictions on the number of objects that can be processed at one time (usually 100). Zenpy makes no attempt to regulate this. Most endpoints will throw an `APIException` if that limit is exceeded, however some simply process the first N objects and silently discard the rest. 


### Caching

Zenpy maintains several caches to prevent unecessary API calls. 

If we turn DEBUG on, we can see Zenpy's caching in action. The code:

```python
print zenpy.users(id=1159307768).name
print zenpy.users(id=1159307768).name
```

Outputs:
```
DEBUG - Cache MISS: [User 1159307768]
DEBUG - GET: https://testing23.zendesk.com/api/v2/users/1159307768.json/?include=organizations,abilities,roles,identities,groups
DEBUG - Caching 1 Groups 
DEBUG - Caching: [User 1159307768]
DEBUG - Caching 1 Organizations 
Face Toe
DEBUG - Cache HIT: [User 1159307768]
Face Toe
```
There a few things to note here. We can see when the user was first requested it was not in the cache, which led to an API call. The GET request which was generated requests the user, but it also adds an `include` directive to pull related objects which led to a Group and Organization object being cached as well. This is called Sideloading by Zendesk, and Zenpy takes advantage of it wherever it can. We can see that the next time the user was requested it was found in the cache and no API call was generated. 

### TO DO
Cover all parts of the API properly.

### Contributions
Contributions are very welcome. 




 







