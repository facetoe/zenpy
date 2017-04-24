from abc import abstractmethod


from zenpy.lib.exception import ZenpyException
from zenpy.lib.generator import SearchResultGenerator, ZendeskResultGenerator, ChatResultGenerator
from zenpy.lib.util import as_singular, as_plural


class ResponseHandler(object):
    def __init__(self, api):
        self.api = api

    @staticmethod
    @abstractmethod
    def applies_to(api, response):
        pass

    @abstractmethod
    def deserialize(self, response_json):
        pass

    @abstractmethod
    def build(self, response):
        pass


class GenericResponseHandler(ResponseHandler):
    @staticmethod
    def applies_to(api, response):
        try:
            return 'zendesk.com' in response.request.url and response.json()
        except ValueError:
            return False

    def deserialize(self, response_json):
        """
        Locate and deserialize all objects in the returned JSON. 
        
        Return a dict keyed by object_type. If the key is plural, the value will be a list,
        if it is singular, the value will be an object of that type. 
        :param response_json: 
        """
        response_objects = dict()
        if all((t in response_json for t in ('ticket', 'audit'))):
            response_objects["ticket_audit"] = self.api._deserializer.object_from_json("ticket_audit",
                                                                                       response_json)

        # Locate and store the single objects.
        for zenpy_object_name in self.api._deserializer.class_mapping:
            if zenpy_object_name in response_json:
                zenpy_object = self.api._deserializer.object_from_json(zenpy_object_name,
                                                                       response_json[zenpy_object_name])
                response_objects[zenpy_object_name] = zenpy_object

        # Locate and store the collections of objects.
        for key, value in response_json.items():
            if isinstance(value, list):
                zenpy_object_name = as_singular(key)
                if zenpy_object_name in self.api._deserializer.class_mapping:
                    response_objects[key] = []
                    for object_json in response_json[key]:
                        zenpy_object = self.api._deserializer.object_from_json(zenpy_object_name, object_json)
                        response_objects[key].append(zenpy_object)
        return response_objects

    def build(self, response):
        """
        Deserialize the returned objects and return either a single Zenpy object, or a ResultGenerator in 
        the case of multiple results. 

        :param response: the requests Response object.
        """
        response_json = response.json()

        zenpy_objects = self.deserialize(response_json)

        # Collection of objects (eg, users/tickets)
        plural_object_type = as_plural(self.api.object_type)
        if plural_object_type in zenpy_objects:
            return ZendeskResultGenerator(self, response_json)

        # Here the response matches the API object_type, seems legit.
        if self.api.object_type in zenpy_objects:
            return zenpy_objects[self.api.object_type]

        # Could be anything, if we know of this object then return it.
        for zenpy_object_name in self.api._deserializer.class_mapping:
            if zenpy_object_name in zenpy_objects:
                return zenpy_objects[zenpy_object_name]

        # Maybe a collection of known objects?
        for zenpy_object_name in self.api._deserializer.class_mapping:
            plural_zenpy_object_name = as_plural(zenpy_object_name)
            if plural_zenpy_object_name in zenpy_objects:
                return ZendeskResultGenerator(self, response_json)

        # Bummer, bail out with an informative message.
        raise ZenpyException("Unknown Response: " + str(response_json))


class HTTPOKResponseHandler(ResponseHandler):
    @staticmethod
    def applies_to(api, response):
        return response.status_code == 200

    def deserialize(self, response_json):
        raise NotImplementedError("HTTPOKResponseHandler cannot handle deserialization")

    def build(self, response):
        return response


class DeleteResponseHandler(GenericResponseHandler):
    @staticmethod
    def applies_to(api, response):
        return response.status_code == 204

    def deserialize(self, response_json):
        raise NotImplementedError("Deserialize is not implemented for DELETE")

    def build(self, response):
        return response


class SearchResponseHandler(GenericResponseHandler):
    @staticmethod
    def applies_to(api, response):
        try:
            return 'results' in response.json()
        except ValueError:
            return False

    def build(self, response):
        return SearchResultGenerator(self, response.json())


class CombinationResponseHandler(GenericResponseHandler):
    @staticmethod
    def applies_to(api, response):
        try:
            response_json = response.json()
            if 'job_status' in response_json:
                return True
            elif 'ticket' in response_json and 'audit' in response_json:
                return True
        except ValueError:
            return False

    def build(self, response):
        zenpy_objects = self.deserialize(response.json())

        # JobStatus responses also include a ticket key so treat it specially.
        if 'job_status' in zenpy_objects:
            return zenpy_objects['job_status']

        # TicketAudit responses are another special case containing both
        # a ticket and audit key.
        if 'ticket' and 'audit' in zenpy_objects:
            return zenpy_objects['ticket_audit']
        raise ZenpyException("Could not process response: {}".format(response))


class TagResponseHandler(ResponseHandler):
    @staticmethod
    def applies_to(api, response):
        _, params = response.request.url.split(api.api_prefix)
        return params.endswith('tags.json')

    def deserialize(self, response_json):
        return response_json['tags']

    def build(self, response):
        return self.deserialize(response.json())


class ChatResponseHandler(ResponseHandler):
    @staticmethod
    def applies_to(api, response):
        _, endpoint_name = response.request.url.split(api.api_prefix)
        return endpoint_name.startswith('/chats')

    def deserialize(self, response_json):
        chats = list()
        if 'chats' in response_json:
            chat_list = response_json['chats']
        elif 'docs' in response_json:
            chat_list = response_json['docs'].values()
        else:
            raise ZenpyException("Unexpected response: {}".format(response_json))
        for chat in chat_list:
            chats.append(self.api.deserializer.object_from_json('chat', chat))
        return chats

    def build(self, response):
        response_json = response.json()
        if 'chats' in response_json or 'docs' in response_json:
            return ChatResultGenerator(self, response_json)
        else:
            return self.api.deserializer.object_from_json('chat', response_json)


class AccountResponseHandler(ResponseHandler):
    @staticmethod
    def applies_to(api, response):
        _, endpoint_name = response.request.url.split(api.api_prefix)
        return endpoint_name.startswith('/account')

    def deserialize(self, response_json):
        return self.api._deserializer.object_from_json('account', response_json)

    def build(self, response):
        return self.deserialize(response.json())
