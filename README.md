# zenpy
Python wrapper for the Zendesk API

## About
Zenpy is a Python wrapper for the Zendesk API. The goal of the project is to make it possible to write clean, fast, Pythonic code when interacting with Zendesk progmatically. The wrapper tries to keep API calls to a minimum. Wherever it makes sense objects are cached, and attributes of objects that would trigger an API call are evaluated lazily. 

It currently supports reading from most endpoints, however writing to the API is coming soon.

The documentation is at this point nonexistent but I hope to write some soon.


### Usage - Top Level
First, create a Zenpy object:
```python
zenpy = Zenpy('somedomain', 'youremail', 'yourtoken')
```

The Zenpy object contains methods for accessing the following top level API endpoints: `search`, `groups`, `users`, `organizations` and `tickets`. The `groups`, `users`, `organizations` and `tickets` top level endpoints aren't that amazing, and they can be called in one of two ways - no arguments returns all results (as a generator):

```python
for user in zenpy.users():
	print user.name
```

And called with an ID returns the object with that ID:

```python
print zenpy.users(id=1159307768).name
```

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

A more interesting top level endpoint is the `search` endpoint. Zenpy defines several keywords which map to the Zendesk search documentation:

```
greater_than = >
less_than = <
*_after = after this time
*_before = before this time
```
Here is an example which shows these keywords in action:
```python
yesterday = datetime.now() - timedelta(days=1)
for ticket in zenpy.search(type='ticket', status_greater_than='new', created_after=yesterday):
	print ticket.subject
```

An example of searching for tickets assigned to a user:
```python
for ticket in zenpy.search(type='ticket', assignee='Face Toe'):
	print ticket.subject
```
The `search` endpoint should support all search parameters defined by Zendesk. 


### Usage - Lower Level
In addition to the top level endpoints available from the Zenpy object, there are also many second level endpoints accessible from the `Api` object contained within Zenpy. Here is an example of using this object to loop over all comments in a ticket:

```python
for comment in zenpy.api.tickets.comments(id=12):
	print comment.body
```

It is important to note that the ID passed to these second level endpoints is always the top level item id. So in this example it is a `ticket` ID which is passed. This is true for other second level endpoints. Here we query all groups that a user is a part of, passing in the `user` ID:

```python
for group in zenpy.api.users.groups(id=1159307768):
	print group.name
```

Here is an example that downloads all attachments in a ticket except those suffixed by .gif:

```python
for comment in zenpy.api.tickets.comments(id=12):
	comment.save_attachments(out_path='/tmp', exlude_suffixs=['gif'])
```

These second level endpoints are not yet stable, so to find out exactly what is available it is best to look at the `Endpoint` object in `lib/endpoint.py`.


### TO DO
The biggest thing is to support writing to the API. 

 ### Contributions
Contributions are very welcome. 




 





