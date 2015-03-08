# zenpy
Python wrapper for the Zendesk API

## Usage

Create a Zenpy object:

```python
    zenpy = Zenpy(subdomain=subdomain, email=email, token=token)
```

Query an API endpoint to obtain an ApiResponse:

```python
    api_response = zenpy.tickets(id=3)
    => <zenpy.api.ApiResponse object at 0x7fd056947610>
```


The ApiResponse contains the full JSON returned by the API:

```python
    print type(api_response.response_json)
    => <type 'dict'>
```


Along with the number of results returned:

```python
    print "The query returned %s results" % api_response.count
    => The query returned 1 results
```
    
And two methods for accessing the returned objects: `one()` and `all()`. 

`one()` returns a single object:
   
 ```python 
    # If there are more than one result, a TooManyResults exception is raised
    print type(api_response.one())
    => <class 'zenpy.api_object.Ticket'>
```

`all()` returns a generator:

```python
    print type(api_response.all())
    => <class 'zenpy.api_object.ApiCallGenerator'>
```
    
## API Endpoints

The API supports the following endpoints:

    * /users
    * /tickets
    * /groups
    * /search
    * /comments
    
See the documentation for the endpoint for the paramaters it accepts.


## Api Objects

The API objects are created dynamically at runtime. For the most part the attributes of these objects 
are exactly the same as the keys in the JSON returned by the Zendesk API, with one exception. Anything that
ends with `_id` in the JSON will not have this suffix, and will return an object instead of an ID:

```python
        api_response = zenpy.tickets(id=3)
        ticket = api_response.one()
        
        print type(ticket.assignee)
        print "Assignee: [%s]" % ticket.assignee.name

        => <class 'zenpy.api_object.User'>
        => Assignee: [Face Toe]
```

Dates and times are returned as datetime objects instead of strings:

```python
        print type(ticket.created_at)
        print ticket.created_at
        
        => <type 'datetime.datetime'>
        => 2015-03-08 04:58:22+00:00
```
For the most part, additional API calls are not made until the object is accessed:

```python
    # Returns a generator
    print type(ticket.comments)

    => INFO - Querying endpoint: https://testapisupport.zendesk.com/api/v2/tickets/3.json
    => <class 'zenpy.api_object.ApiCallGenerator'>


    # Fires another API call to retrieve the comments
    for comment in ticket.comments:
        print "Comment: [%s]" % comment.body

    => INFO - Querying endpoint: https://testapisupport.zendesk.com/api/v2/tickets/4.json
    => INFO - Making generator request to: https://testapisupport.zendesk.com/api/v2/tickets/4/comments.json
    => Comment: [Comment on a ticket]
```
    
    
## Caching

All objects except for Tickets are cached. At the moment the cache is very dumb and is never cleared. 


## Examples

### Download all PNG attachments for a ticket:

```python
api_response = zenpy.tickets(id=2)
ticket = api_response.one()
for comment in ticket.comments:
    for attachment in comment.attachments:
        with open('/tmp/' + attachment.file_name, 'w+') as f:
            f.write(attachment.content)
```

### Print total ticket count:

```python
print zenpy.tickets().count
```

### Print email for all users who's name starts with "face"

```python
for user in zenpy.search(name='face*').all():
    print user.email
```

### Search on multiple parameters:

```python
yesterday = date.today() - timedelta(hours=24)
response = zenpy.search(assignee="Face Toe", 
                        tags='special_tag', 
                        priority='high', 
                        created_after=yesterday)
```



    

    




