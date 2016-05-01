# Zenpy

Zenpy is a Python wrapper for the Zendesk API. The goal of the project is to make it possible to write clean, fast, Pythonic code when interacting with Zendesk progmatically. The wrapper tries to keep API calls to a minimum. Wherever it makes sense objects are cached, and attributes of objects that would trigger an API call are evaluated lazily. 

The wrapper supports both reading and writing from the API.

Zenpy supports both Python2 and Python3. 

Zenpy is still in beta, so please report any bugs!

## Quickstart

```python
# Create a Zenpy object
zenpy = Zenpy(**credentials)

# Create a new ticket
zenpy.tickets.create(Ticket(subject="Important", description="Thing"))

# Perform a simple search
for ticket in zenpy.search("party", type='ticket', assignee="face"):
    print(ticket)
```

## Documentation

Check out the [documentation](http://docs.facetoe.com.au/) for more info.

### Contributions
Contributions are very welcome. 


