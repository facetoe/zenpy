import collections
from abc import abstractmethod

from zenpy.lib.api_objects.chat_objects import Billing, Plan
from zenpy.lib.cache import delete_from_cache
from zenpy.lib.exception import ZenpyException
from zenpy.lib.util import get_object_type, as_plural


class Request(object):
    def __init__(self, api):
        self.api = api

    def perform(self, http_method, *args, **kwargs):
        http_method = http_method.lower()
        if http_method == 'put':
            return self.put(*args, **kwargs)
        elif http_method == 'post':
            return self.post(*args, **kwargs)
        elif http_method == 'delete':
            return self.delete(*args, **kwargs)
        raise ZenpyException("{} cannot handle HTTP method: {}".format(self.__class__.__name__, http_method))

    @abstractmethod
    def put(self, api_objects, *args, **kwargs):
        pass

    @abstractmethod
    def post(self, api_objects, *args, **kwargs):
        pass

    @abstractmethod
    def delete(self, api_objects, *args, **kwargs):
        pass


class ZendeskRequest(Request):
    def _build_payload(self, api_objects):
        if isinstance(api_objects, collections.Iterable):
            payload_key = as_plural(self.api.object_type)
        else:
            payload_key = self.api.object_type
        return {payload_key: self.api._serialize(api_objects)}

    def check_type(self, zenpy_objects):
        """ Ensure the passed type matches this API's object_type. """
        expected_type = self.api._deserializer.class_for_type(self.api.object_type)
        if not isinstance(zenpy_objects, collections.Iterable):
            zenpy_objects = [zenpy_objects]
        for zenpy_object in zenpy_objects:
            if type(zenpy_object) is not expected_type:
                raise ZenpyException(
                    "Invalid type - expected {} found {}".format(expected_type, type(zenpy_object))
                )


class GenericCRUDRequest(ZendeskRequest):
    def post(self, api_objects, *args, **kwargs):
        self.check_type(api_objects)
        if isinstance(api_objects, collections.Iterable):
            kwargs['create_many'] = True

        payload = self._build_payload(api_objects)
        url = self.api._build_url(self.api.endpoint(*args, **kwargs))
        return self.api._post(url, payload)

    def put(self, api_objects, *args, **kwargs):
        self.check_type(api_objects)
        if isinstance(api_objects, collections.Iterable):
            kwargs['update_many'] = True
        else:
            kwargs['id'] = api_objects.id

        payload = self._build_payload(api_objects)
        url = self.api._build_url(self.api.endpoint(*args, **kwargs))
        return self.api._put(url, payload=payload)

    def delete(self, api_objects, *args, **kwargs):
        self.check_type(api_objects)
        if isinstance(api_objects, collections.Iterable):
            kwargs['destroy_ids'] = [i.id for i in api_objects]
        else:
            kwargs['id'] = api_objects.id
        payload = self._build_payload(api_objects)
        url = self.api._build_url(self.api.endpoint(*args, **kwargs))
        response = self.api._delete(url, payload=payload)
        delete_from_cache(api_objects)
        return response


class SuspendedTicketRequest(ZendeskRequest):
    def post(self, api_objects, *args, **kwargs):
        raise NotImplementedError("POST is not implemented for suspended tickets!")

    def put(self, tickets, *args, **kwargs):
        self.check_type(tickets)
        endpoint_kwargs = dict()
        if isinstance(tickets, collections.Iterable):
            endpoint_kwargs['recover_ids'] = [i.id for i in tickets]
            endpoint = self.api.endpoint
        else:
            endpoint_kwargs['id'] = tickets.id
            endpoint = self.api.endpoint.recover
        payload = self._build_payload(tickets)
        url = self.api._build_url(endpoint(**endpoint_kwargs))
        return self.api._put(url, payload=payload)

    def delete(self, tickets, *args, **kwargs):
        self.check_type(tickets)
        endpoint_kwargs = dict()
        if isinstance(tickets, collections.Iterable):
            endpoint_kwargs['destroy_ids'] = [i.id for i in tickets]
        else:
            endpoint_kwargs['id'] = tickets.id
        payload = self._build_payload(tickets)
        url = self.api._build_url(self.api.endpoint(**endpoint_kwargs))
        response = self.api._delete(url, payload=payload)
        delete_from_cache(tickets)
        return response


class TagRequest(Request):
    def post(self, tags, *args, **kwargs):
        return self.modify_tags(self.api._post, tags, *args)

    def put(self, tags, *args, **kwargs):
        return self.modify_tags(self.api._put, tags, *args)

    def delete(self, tags, *args, **kwargs):
        return self.modify_tags(self.api._delete, tags, *args)

    def modify_tags(self, http_method, tags, id):
        url = self.api._build_url(self.api.endpoint.tags(id=id))
        payload = dict(tags=tags)
        return http_method(url, payload=payload)


class RateRequest(Request):
    def post(self, rating, *args, **kwargs):
        url = self.api._build_url(self.api.endpoint.satisfaction_ratings(*args))
        payload = {get_object_type(rating): self.api._serialize(rating)}
        return self.api._post(url, payload=payload)

    def put(self, api_objects, *args, **kwargs):
        raise NotImplementedError("PUT is not implemented for RateRequest!")

    def delete(self, api_objects, *args, **kwargs):
        raise NotImplementedError("DELETE is not implemented for RateRequest!")


class UserIdentityRequest(ZendeskRequest):
    def post(self, user, identity):
        payload = self._build_payload(identity)
        url = self.api._build_url(self.api.endpoint(id=user))
        return self.api._post(url, payload=payload)

    def put(self, endpoint, user, identity):
        payload = self._build_payload(identity)
        url = self.api._build_url(endpoint(user, identity))
        return self.api._put(url, payload=payload)

    def delete(self, user, identity):
        payload = self._build_payload(identity)
        url = self.api._build_url(self.api.endpoint.delete(user, identity))
        return self.api._delete(url, payload=payload)


class AccountRequest(Request):
    def put(self, chat_object, *args, **kwargs):
        return self.create_or_update(self.api._put, chat_object)

    def post(self, chat_object, *args, **kwargs):
        return self.create_or_update(self.api._post, chat_object)

    def delete(self, chat_object, *args, **kwargs):
        raise NotImplementedError("Cannot delete accounts!")

    def create_or_update(self, http_method, chat_object):
        if type(chat_object) not in (Billing, Plan):
            raise ZenpyException("Invalid type - expected either Billing or Plan, found: {}".format(chat_object))
        payload = {get_object_type(chat_object): self.api._serialize(chat_object)}
        return http_method(self.api._build_url(self.api.endpoint()), payload=payload)
