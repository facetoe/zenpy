# Contributors Guide

Looking to hack on Zenpy? Awesome! In this guide I will explain how things hang together to (hopefully) get you started.

## Zenpy Concepts and Terminology

There are few concepts that go together to make up the wrapper. If they make sense, it should be pretty easy to change things.

### Endpoints

Endpoints are callable classes that know how to take some input and return as output the correct path and parameters to query the Zendesk API with. For example, if the ticket endpoint is passed a list of ids to delete, it would output something along the lines of `tickets/destroy_many.json?ids=1,2,3,4,5`. That's all it needs to do.

The `zenpy/lib/endpoint.py` file contains the factory class `EndpointFactory`. This encapsulates all the endpoints and structures them to mirror the structure of Zendesk's API.

### Apis

An `Api` in Zenpy is class that knows how to perform operations on a particular Zendesk endpoint or object. For example, the `TicketApi` knows how to manipulate `Tickets`, and exposes methods such as `merge` for merging `Tickets`.

All the various `Api` classes are encapsulated and exposed to the user through the `Zenpy` class located in `zenpy/__init__.py`.

### Request Handlers

A RequestHandler knows how to make a POST, PUT or DELETE request to Zendesk with the correct format. There are several generic RequestHandlers that handle most cases, however it is occasionally necessary to write new ones to handle edge cases/inconsistencies in the expected format (especially for the ChatApi).

### Response Handlers

A `ResponseHandler` knows how to identify a response that it can handle, and also how to deserealize it from JSON and return the correct type to the user. When a response is returned from Zendesk, each ResponseHandler is tried in order and the first one that matches is executed. ResponseHandlers should always be ordered from most specific to most generic.

### Api Objects

The Zendesk API contains many objects. I am way too lazy to write the code for them all, so I wrote a tool to generate Python classes from JSON instead. It uses Jinja templating and can be found in `tools`. It can be executed from the `tools` directory as follows (requires Python3):

```bash
./gen_classes.py --spec-path ../specification/ --doc-json doc_dict.json -o ../zenpy/lib/
```

Creating a new object is as simple as creating a file in the `zenpy/specification` directory and executing the tool. Once that's done, it will also need to be added to the relevant mapping class in `zenpy/lib/mapping.py`.

For the objects themselves, the idea is that any attribute of an object that can be presented in a more user friendly manner should be converted before being returned. So for example strings representing time should be presented as `datetime` objects, id's for linked objects should be fetched and deserialized and responses that involve pagination should be exposed as generators.

### Debugging

During your work on project contribution or your own project it may be useful to track `zenpy` requests and cache use. Some logging implemented in `zenpy`, so you can switch it on. To do it add this to you application after `zenpy_client` init:

```python
import logging, sys
log = logging.getLogger()
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)
logging.getLogger("requests").setLevel(logging.WARNING)
```

## Putting it all together.

The general flow of execution for a POST, PUT, DELETE action is as follows:

Api -> RequestHandler -> Endpoint -> HTTP METHOD -> ResponseHandler -> (ApiObject or ResultGenerator) returned to user. There are a few steps in between like checking the response, caching objects etc, but that's a general idea.

For a GET request, it is as above except the caches are first checked and a request is only generated if the object is not present.

Anyway, hopefully, this has been a helpful overview of how Zenpy works. If you have any questions, just ask!
