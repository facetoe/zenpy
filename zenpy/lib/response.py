from abc import abstractmethod

from zenpy.lib.exception import ZenpyException
from zenpy.lib.generator import SearchResultGenerator, ZendeskResultGenerator, ChatResultGenerator, ViewResultGenerator, \
    TicketAuditGenerator, ChatIncrementalResultGenerator
from zenpy.lib.util import as_singular, as_plural, get_endpoint_path


class ResponseHandler(object):
    """
    A ResponseHandler knows the type of response it can handle, how to deserialize it and
    also how to build the correct return type for the data received.

    Note: it is legal for multiple handlers to know how to process the same response. The
    handler that is ultimately chosen is determined by the order in the Api._response_handlers tuple.
    When adding a new handler, it is important to place the most general handlers last, and the most
    specific first.
    """

    def __init__(self, api, object_mapping=None):
        self.api = api
        self.object_mapping = object_mapping or api._object_mapping

    @staticmethod
    @abstractmethod
    def applies_to(api, response):
        """ Subclasses should return True if they know how to deal with this response. """

    @abstractmethod
    def deserialize(self, response_json):
        """ Subclasses should implement the necessary logic to deserialize the passed JSON and return the result. """

    @abstractmethod
    def build(self, response):
        """
        Subclasses should deserialize the objects here and return the correct type to the user.
        Usually this boils down to deciding whether or not we should return a ResultGenerator
        of a particular type, a list of objects or a single object.
        """


class GenericZendeskResponseHandler(ResponseHandler):
    """ The most generic handler for responses from the Zendesk API. """

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
            response_objects["ticket_audit"] = self.object_mapping.object_from_json(
                "ticket_audit",
                response_json
            )

        # Locate and store the single objects.
        for zenpy_object_name in self.object_mapping.class_mapping:
            if zenpy_object_name in response_json:
                zenpy_object = self.object_mapping.object_from_json(
                    zenpy_object_name,
                    response_json[zenpy_object_name]
                )
                response_objects[zenpy_object_name] = zenpy_object

        # Locate and store the collections of objects.
        for key, value in response_json.items():
            if isinstance(value, list):
                zenpy_object_name = as_singular(key)
                if zenpy_object_name in self.object_mapping.class_mapping:
                    response_objects[key] = []
                    for object_json in response_json[key]:
                        zenpy_object = self.object_mapping.object_from_json(
                            zenpy_object_name,
                            object_json
                        )
                        response_objects[key].append(zenpy_object)
        return response_objects

    def build(self, response):
        """
        Deserialize the returned objects and return either a single Zenpy object, or a ResultGenerator in
        the case of multiple results.

        :param response: the requests Response object.
        """
        response_json = response.json()

        # Special case for ticket audits.
        if get_endpoint_path(self.api, response).startswith('/ticket_audits.json'):
            return TicketAuditGenerator(self, response_json)

        zenpy_objects = self.deserialize(response_json)

        # Collection of objects (eg, users/tickets)
        plural_object_type = as_plural(self.api.object_type)
        if plural_object_type in zenpy_objects:
            return ZendeskResultGenerator(self, response_json, response_objects=zenpy_objects[plural_object_type])

        # Here the response matches the API object_type, seems legit.
        if self.api.object_type in zenpy_objects:
            return zenpy_objects[self.api.object_type]

        # Could be anything, if we know of this object then return it.
        for zenpy_object_name in self.object_mapping.class_mapping:
            if zenpy_object_name in zenpy_objects:
                return zenpy_objects[zenpy_object_name]

        # Maybe a collection of known objects?
        for zenpy_object_name in self.object_mapping.class_mapping:
            plural_zenpy_object_name = as_plural(zenpy_object_name)
            if plural_zenpy_object_name in zenpy_objects:
                return ZendeskResultGenerator(self, response_json, object_type=plural_zenpy_object_name)

        # Bummer, bail out.
        raise ZenpyException("Unknown Response: " + str(response_json))


class HTTPOKResponseHandler(ResponseHandler):
    """ The name is on the box, handles 200 responses. """

    @staticmethod
    def applies_to(api, response):
        return response.status_code == 200

    def deserialize(self, response_json):
        raise NotImplementedError("HTTPOKResponseHandler cannot handle deserialization")

    def build(self, response):
        return response


class ViewResponseHandler(GenericZendeskResponseHandler):
    """
    Handles the various responses returned by the View endpoint.
    """

    @staticmethod
    def applies_to(api, response):
        return get_endpoint_path(api, response).startswith('/views')

    def deserialize(self, response_json):
        deserialized_response = super(ViewResponseHandler, self).deserialize(response_json)
        if 'rows' in response_json:
            views = list()
            for row in response_json['rows']:
                views.append(self.object_mapping.object_from_json('view_row', row))
            return views
        elif 'views' in deserialized_response:
            return deserialized_response['views']
        elif 'tickets' in deserialized_response:
            return deserialized_response['tickets']
        elif 'view_counts' in deserialized_response:
            return deserialized_response['view_counts']
        elif 'view_count' in deserialized_response:
            return deserialized_response['view_count']
        elif 'export' in deserialized_response:
            return deserialized_response['export']
        else:
            return deserialized_response['view']

    def build(self, response):
        response_json = response.json()
        if any([key in response_json for key in ['rows', 'view_counts', 'tickets']]):
            return ViewResultGenerator(self, response_json)
        else:
            return self.deserialize(response_json)


class DeleteResponseHandler(GenericZendeskResponseHandler):
    """ Yup, handles 204 No Content. """

    @staticmethod
    def applies_to(api, response):
        return response.status_code == 204

    def deserialize(self, response_json):
        raise NotImplementedError("Deserialize is not implemented for DELETE")

    def build(self, response):
        return response


class SearchResponseHandler(GenericZendeskResponseHandler):
    """ Handles Zendesk search results. """

    @staticmethod
    def applies_to(api, response):
        try:
            return 'results' in response.json()
        except ValueError:
            return False

    def build(self, response):
        return SearchResultGenerator(self, response.json())

class CountResponseHandler(GenericZendeskResponseHandler):
    """ Handles Zendesk search results counts. """

    @staticmethod
    def applies_to(api, response):
        try:
            response_json = response.json()
            return len(response_json) == 1 and 'count' in response_json
        except ValueError:
            return False

    def build(self, response):
        return response.json()['count']


class CombinationResponseHandler(GenericZendeskResponseHandler):
    """ Handles a few special cases where the return type is made up of two objects. """

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

class JobStatusesResponseHandler(GenericZendeskResponseHandler):

    @staticmethod
    def applies_to(api, response):
        try:
            response_json = response.json()
            if 'job_statuses' in response_json:
                return True
        except ValueError:
            return False

    def build(self, response):
        response_objects = {'job_statuses': []}
        for object_json in response.json()['job_statuses']:
            zenpy_object = self.object_mapping.object_from_json(
                'job_status',
                object_json
            )
            response_objects['job_statuses'].append(zenpy_object)
        return response_objects

class TagResponseHandler(ResponseHandler):
    """ Tags aint complicated, just return them. """

    @staticmethod
    def applies_to(api, response):
        _, params = response.request.url.split(api.api_prefix)
        return params.endswith('tags.json')

    def deserialize(self, response_json):
        return response_json['tags']

    def build(self, response):
        return self.deserialize(response.json())


class SlaPolicyResponseHandler(GenericZendeskResponseHandler):
    @staticmethod
    def applies_to(api, response):
        return get_endpoint_path(api, response).startswith('/slas')

    def deserialize(self, response_json):
        if 'definitions' in response_json:
            definitions = self.object_mapping.object_from_json('definitions', response_json['definitions'])
            return dict(definitions=definitions)
        return super(SlaPolicyResponseHandler, self).deserialize(response_json)

    def build(self, response):
        response_json = response.json()
        response_objects = self.deserialize(response_json)
        if 'sla_policies' in response_objects:
            return ZendeskResultGenerator(self, response.json(), response_objects=response_objects['sla_policies'])
        elif 'sla_policy' in response_objects:
            return response_objects['sla_policy']
        elif response_objects:
            return response_objects['definitions']
        raise ZenpyException("Could not handle response: {}".format(response_json))


class RequestCommentResponseHandler(GenericZendeskResponseHandler):
    @staticmethod
    def applies_to(api, response):
        endpoint_path = get_endpoint_path(api, response)
        return endpoint_path.startswith('/requests') and endpoint_path.endswith('comments.json')

    def deserialize(self, response_json):
        return super(RequestCommentResponseHandler, self).deserialize(response_json)

    def build(self, response):
        response_json = response.json()
        response_objects = self.deserialize(response_json)
        return ZendeskResultGenerator(self, response_json, response_objects['comments'], object_type='comment')


class ChatResponseHandler(ResponseHandler):
    """ Handles Chat responses. """

    @staticmethod
    def applies_to(api, response):
        path = get_endpoint_path(api, response)
        return path.startswith('/chats') or path.startswith('/incremental/chats')

    def deserialize(self, response_json):
        chats = list()
        if 'chats' in response_json:
            chat_list = response_json['chats']
        elif 'docs' in response_json:
            chat_list = response_json['docs'].values()
        else:
            raise ZenpyException("Unexpected response: {}".format(response_json))
        for chat in chat_list:
            chats.append(self.object_mapping.object_from_json('chat', chat))
        return chats

    def build(self, response):
        response_json = response.json()
        if 'chats' in response_json or 'docs' in response_json:
            if 'next_page' in response_json:
                return ChatIncrementalResultGenerator(self, response_json)
            else:
                return ChatResultGenerator(self, response_json)
        else:
            return self.object_mapping.object_from_json('chat', response_json)


class AccountResponseHandler(ResponseHandler):
    """ Handles Chat API Account responses. """

    @staticmethod
    def applies_to(api, response):
        _, endpoint_name = response.request.url.split(api.api_prefix)
        return endpoint_name.startswith('/account')

    def deserialize(self, response_json):
        return self.object_mapping.object_from_json('account', response_json)

    def build(self, response):
        return self.deserialize(response.json())


class ChatSearchResponseHandler(ResponseHandler):
    """ Yep, handles Chat API search responses. """

    @staticmethod
    def applies_to(api, response):
        return get_endpoint_path(api, response).startswith('/chats/search')

    def deserialize(self, response_json):
        search_results = list()
        for result in response_json['results']:
            search_results.append(self.object_mapping.object_from_json('search_result', result))
        return search_results

    def build(self, response):
        return ChatResultGenerator(self, response.json())


class ChatApiResponseHandler(ResponseHandler):
    """
    Base class for Chat API responses that follow the same pattern.
    Subclasses need only define object type and implement applies_to().
    """
    object_type = None

    def deserialize(self, response_json):
        agents = list()
        if isinstance(response_json, dict):
            return self.object_mapping.object_from_json(self.object_type, response_json)
        else:
            for agent in response_json:
                agents.append(self.object_mapping.object_from_json(self.object_type, agent))
            return agents

    def build(self, response):
        return self.deserialize(response.json())


class AgentResponseHandler(ChatApiResponseHandler):
    object_type = 'agent'

    @staticmethod
    def applies_to(api, response):
        return get_endpoint_path(api, response).startswith('/agents')


class VisitorResponseHandler(ChatApiResponseHandler):
    object_type = 'visitor'

    @staticmethod
    def applies_to(api, response):
        return get_endpoint_path(api, response).startswith('/visitors')


class ShortcutResponseHandler(ChatApiResponseHandler):
    object_type = 'shortcut'

    @staticmethod
    def applies_to(api, response):
        return get_endpoint_path(api, response).startswith('/shortcuts')


class TriggerResponseHandler(ChatApiResponseHandler):
    object_type = 'trigger'

    @staticmethod
    def applies_to(api, response):
        return get_endpoint_path(api, response).startswith('/triggers')


class BanResponseHandler(ChatApiResponseHandler):
    object_type = 'ban'

    @staticmethod
    def applies_to(api, response):
        return get_endpoint_path(api, response).startswith('/bans')


class DepartmentResponseHandler(ChatApiResponseHandler):
    object_type = 'department'

    @staticmethod
    def applies_to(api, response):
        return get_endpoint_path(api, response).startswith('/departments')


class GoalResponseHandler(ChatApiResponseHandler):
    object_type = 'goal'

    @staticmethod
    def applies_to(api, response):
        return get_endpoint_path(api, response).startswith('/goals')


class MissingTranslationHandler(ResponseHandler):
    @staticmethod
    def applies_to(api, response):
        return 'translations/missing.json' in get_endpoint_path(api, response)

    def build(self, response):
        return self.deserialize(response.json())

    def deserialize(self, response_json):
        return response_json['locales']
