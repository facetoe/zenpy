import collections
import os
from abc import abstractmethod

from zenpy.lib.api_objects import BaseObject, Ticket
from zenpy.lib.api_objects.chat_objects import Shortcut, Trigger
from zenpy.lib.cache import delete_from_cache
from zenpy.lib.endpoint import EndpointFactory
from zenpy.lib.exception import ZenpyException
from zenpy.lib.util import get_object_type, as_plural


class RequestHandler(object):
    """
    Abstraction of a request to either the Zendesk API or the Chat API. Only POST, PUT and
    DELETE are handled. Subclasses implement the logic needed to correctly serialize the request
    to JSON and send off to the relevant API.
    """

    def __init__(self, api):
        self.api = api

    @abstractmethod
    def put(self, api_objects, *args, **kwargs):
        pass

    @abstractmethod
    def post(self, api_objects, *args, **kwargs):
        pass

    @abstractmethod
    def delete(self, api_objects, *args, **kwargs):
        pass


class BaseZendeskRequest(RequestHandler):
    """
    Base class for Zendesk requests. Provides a few handy methods.
    """

    def build_payload(self, api_objects):
        if isinstance(api_objects, collections.Iterable):
            payload_key = as_plural(self.api.object_type)
        else:
            payload_key = self.api.object_type
        return {payload_key: self.api._serialize(api_objects)}

    def check_type(self, zenpy_objects):
        """ Ensure the passed type matches this API's object_type. """
        expected_type = self.api._object_mapping.class_for_type(self.api.object_type)
        if not isinstance(zenpy_objects, collections.Iterable):
            zenpy_objects = [zenpy_objects]
        for zenpy_object in zenpy_objects:
            if type(zenpy_object) is not expected_type:
                raise ZenpyException(
                    "Invalid type - expected {} found {}".format(expected_type, type(zenpy_object))
                )


class CRUDRequest(BaseZendeskRequest):
    """
    Generic CRUD request. Most CRUD operations are handled by this class.
    """

    def post(self, api_objects, *args, **kwargs):
        self.check_type(api_objects)

        create_or_update = kwargs.pop('create_or_update', False)
        create = kwargs.pop('create', False)
        if isinstance(api_objects, collections.Iterable) and create_or_update:
            kwargs['create_or_update_many'] = True
            endpoint = self.api.endpoint.create_or_update_many
        elif isinstance(api_objects, collections.Iterable):
            kwargs['create_many'] = True
            endpoint = self.api.endpoint
        elif create_or_update:
            endpoint = self.api.endpoint.create_or_update
        elif create:
            endpoint = self.api.endpoint.create
        else:
            endpoint = self.api.endpoint

        payload = self.build_payload(api_objects)
        url = self.api._build_url(endpoint(*args, **kwargs))
        return self.api._post(url, payload)

    def put(self, api_objects, update_many_external=False, *args, **kwargs):
        self.check_type(api_objects)

        if update_many_external:
            kwargs['update_many_external'] = [o.external_id for o in api_objects]
        elif isinstance(api_objects, collections.Iterable):
            kwargs['update_many'] = True
        else:
            kwargs['id'] = api_objects.id

        payload = self.build_payload(api_objects)
        url = self.api._build_url(self.api.endpoint(*args, **kwargs))
        return self.api._put(url, payload=payload)

    def delete(self, api_objects, destroy_many_external=False, *args, **kwargs):
        self.check_type(api_objects)
        if destroy_many_external:
            kwargs['destroy_many_external'] = [o.external_id for o in api_objects]
        elif isinstance(api_objects, collections.Iterable):
            kwargs['destroy_ids'] = [i.id for i in api_objects]
        else:
            kwargs['id'] = api_objects.id
        payload = self.build_payload(api_objects)
        url = self.api._build_url(self.api.endpoint(*args, **kwargs))
        response = self.api._delete(url, payload=payload)
        delete_from_cache(api_objects)
        return response


class SuspendedTicketRequest(BaseZendeskRequest):
    """
    Handle updating and deleting SuspendedTickets.
    """

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
        payload = self.build_payload(tickets)
        url = self.api._build_url(endpoint(**endpoint_kwargs))
        return self.api._put(url, payload=payload)

    def delete(self, tickets, *args, **kwargs):
        self.check_type(tickets)
        endpoint_kwargs = dict()
        if isinstance(tickets, collections.Iterable):
            endpoint_kwargs['destroy_ids'] = [i.id for i in tickets]
        else:
            endpoint_kwargs['id'] = tickets.id
        payload = self.build_payload(tickets)
        url = self.api._build_url(self.api.endpoint(**endpoint_kwargs))
        response = self.api._delete(url, payload=payload)
        delete_from_cache(tickets)
        return response


class TagRequest(RequestHandler):
    """
    Handle tag operations.
    """

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


class RateRequest(RequestHandler):
    """ Handles submitting ratings. """

    def post(self, rating, *args, **kwargs):
        url = self.api._build_url(self.api.endpoint.satisfaction_ratings(*args))
        payload = {get_object_type(rating): self.api._serialize(rating)}
        return self.api._post(url, payload=payload)

    def put(self, api_objects, *args, **kwargs):
        raise NotImplementedError("PUT is not implemented for RateRequest!")

    def delete(self, api_objects, *args, **kwargs):
        raise NotImplementedError("DELETE is not implemented for RateRequest!")


class UserIdentityRequest(BaseZendeskRequest):
    """ Handle CRUD operations on UserIdentities. """

    def post(self, user, identity):
        payload = self.build_payload(identity)
        url = self.api._build_url(self.api.endpoint(id=user))
        return self.api._post(url, payload=payload)

    def put(self, endpoint, user, identity):
        payload = self.build_payload(identity)
        url = self.api._build_url(endpoint(user, identity))
        return self.api._put(url, payload=payload)

    def delete(self, user, identity):
        payload = self.build_payload(identity)
        url = self.api._build_url(self.api.endpoint.delete(user, identity))
        return self.api._delete(url, payload=payload)


class UploadRequest(RequestHandler):
    """ Handles uploading files to Zendesk. """

    def post(self, fp, token=None, target_name=None):
        if hasattr(fp, 'read'):
            # File-like objects such as:
            #   PY3: io.StringIO, io.TextIOBase, io.BufferedIOBase
            #   PY2: file, io.StringIO, StringIO.StringIO, cStringIO.StringIO

            if not hasattr(fp, 'name') and not target_name:
                raise ZenpyException("upload requires a target file name")
            else:
                target_name = target_name or fp.name

        elif isinstance(fp, str):
            if os.path.isfile(fp):
                fp = open(fp, 'rb')
                target_name = target_name or fp.name
            elif not target_name:
                # Valid string, which is not a path, and without a target name
                raise ZenpyException("upload requires a target file name")

        elif not target_name:
            # Other serializable types accepted by requests (like dict)
            raise ZenpyException("upload requires a target file name")

        url = self.api._build_url(self.api.endpoint.upload(filename=target_name, token=token))
        return self.api._post(url, data=fp, payload={})

    def put(self, api_objects, *args, **kwargs):
        raise NotImplementedError("POST is not implemented fpr UploadRequest!")

    def delete(self, api_objects, *args, **kwargs):
        raise NotImplementedError("DELETE is not implemented fpr UploadRequest!")


class UserMergeRequest(BaseZendeskRequest):
    """ Handles merging two users. """

    def put(self, source, destination):
        self.check_type(destination)
        if issubclass(type(source), BaseObject):
            source = source.id
        if issubclass(type(destination), BaseObject):
            destination = destination.id

        url = self.api._build_url(self.api.endpoint.merge(id=source))
        payload = {self.api.object_type: dict(id=destination)}
        return self.api._put(url, payload=payload)

    def post(self, *args, **kwargs):
        raise NotImplementedError("POST is not implemented for UserMergeRequest!")

    def delete(self, api_objects, *args, **kwargs):
        raise NotImplementedError("DELETE is not implemented for UserMergeRequest!")


class TicketMergeRequest(RequestHandler):
    """ Handles merging one or more tickets.  """

    def post(self, target, source, target_comment=None, source_comment=None):
        if isinstance(target, Ticket):
            target = target.id
        if isinstance(source, Ticket):
            source_ids = [source.id]
        else:
            source_ids = [t.id if isinstance(t, Ticket) else t for t in source]

        payload = dict(
            ids=source_ids,
            target_comment=target_comment,
            source_comment=source_comment
        )
        url = self.api._build_url(self.api.endpoint.merge(id=target))
        return self.api._post(url, payload=payload)

    def put(self, api_objects, *args, **kwargs):
        raise NotImplementedError("PUT is not implemented for TicketMergeRequest!")

    def delete(self, api_objects, *args, **kwargs):
        raise NotImplementedError("DELETE is not implemented fpr TicketMergeRequest!")


class SatisfactionRatingRequest(BaseZendeskRequest):
    """ Handle rating a ticket.  """

    def post(self, ticket_id, satisfaction_rating):
        payload = self.build_payload(satisfaction_rating)
        url = self.api._build_url(EndpointFactory('satisfaction_ratings').create(id=ticket_id))
        return self.api._post(url, payload)

    def put(self, api_objects, *args, **kwargs):
        raise NotImplementedError("PUT is not implemented for SatisfactionRequest!")

    def delete(self, api_objects, *args, **kwargs):
        raise NotImplementedError("DELETE is not implemented fpr SatisfactionRequest!")


class ChatApiRequest(RequestHandler):
    """
    Generic Chat API request. Most CRUD operations on Chat API endpoints are handled by this class.
    """

    def put(self, chat_object):
        identifier = self.get_object_identifier(chat_object)
        value = getattr(chat_object, identifier)
        setattr(chat_object, identifier, None)  # The API freaks out when a identifier is in the JSON
        payload = self.flatten_chat_object(self.api._serialize(chat_object))
        url = self.api._build_url(self.api.endpoint(**{identifier: value}))
        return self.api._put(url, payload=payload)

    def post(self, chat_object):
        payload = self.api._serialize(chat_object)
        return self.api._post(self.api._build_url(self.api.endpoint()), payload=payload)

    def delete(self, chat_object, *args, **kwargs):
        identifier = self.get_object_identifier(chat_object)
        value = getattr(chat_object, identifier)
        url = self.api._build_url(self.api.endpoint(**{identifier: value}))
        return self.api._delete(url)

    def flatten_chat_object(self, chat_object, parent_key=''):
        items = []
        for key, value in chat_object.items():
            new_key = "{}.{}".format(parent_key, key) if parent_key else key
            if isinstance(value, dict):
                items.extend(self.flatten_chat_object(value, new_key).items())
            else:
                items.append((new_key, value))
        return dict(items)

    def get_object_identifier(self, chat_object):
        if type(chat_object) in (Shortcut, Trigger):
            return 'name'
        else:
            return 'id'


class AccountRequest(RequestHandler):
    """ Handle creating and updating Accounts.  """

    def put(self, account):
        payload = self.build_payload(account)
        return self.api._put(self.api._build_url(self.api.endpoint()), payload=payload)

    def post(self, account):
        payload = self.build_payload(account)
        return self.api._post(self.api._build_url(self.api.endpoint()), payload=payload)

    def delete(self, chat_object, *args, **kwargs):
        raise NotImplementedError("Cannot delete accounts!")

    def build_payload(self, account):
        return {get_object_type(account): self.api._serialize(account)}


class PersonRequest(RequestHandler):
    """ Handle CRUD operations on Chat API objects representing people. """

    def put(self, chat_object):
        agent_id = chat_object.id
        chat_object.id = None  # The API freaks out if id is included.
        payload = self.api._serialize(chat_object)
        url = self.api._build_url(self.api.endpoint(id=agent_id))
        return self.api._put(url, payload=payload)

    def post(self, account):
        payload = self.api._serialize(account)
        return self.api._post(self.api._build_url(self.api.endpoint()), payload=payload)

    def delete(self, chat_object):
        url = self.api._build_url(self.api.endpoint(id=chat_object.id))
        return self.api._delete(url)


class AgentRequest(PersonRequest):
    pass


class VisitorRequest(PersonRequest):
    pass


class HelpdeskCommentRequest(BaseZendeskRequest):
    def put(self, endpoint, article, comment):
        url = self.api._build_url(endpoint(article, comment.id))
        payload = self.build_payload(comment)
        return self.api._put(url, payload)

    def post(self, endpoint, article, comment):
        url = self.api._build_url(endpoint(id=article))
        payload = self.build_payload(comment)
        return self.api._post(url, payload)

    def delete(self, endpoint, article, comment):
        url = self.api._build_url(endpoint(article, comment))
        return self.api._delete(url)


class HelpCentreRequest(BaseZendeskRequest):
    def put(self, endpoint, article, api_object):
        url = self.api._build_url(endpoint(article, api_object))
        payload = self.build_payload(api_object)
        return self.api._put(url, payload)

    def post(self, endpoint, article, api_object):
        url = self.api._build_url(endpoint(id=article))
        payload = self.build_payload(api_object)
        return self.api._post(url, payload)

    def delete(self, endpoint, article, api_object):
        url = self.api._build_url(endpoint(article, api_object))
        return self.api._delete(url)


class PostCommentRequest(HelpCentreRequest):
    def build_payload(self, translation):
        return {get_object_type(translation): self.api._serialize(translation)}

    def put(self, endpoint, post, comment):
        url = self.api._build_url(endpoint(post, comment.id))
        payload = self.build_payload(comment)
        return self.api._put(url, payload)


class SubscriptionRequest(HelpCentreRequest):
    def build_payload(self, translation):
        return {get_object_type(translation): self.api._serialize(translation)}


class AccessPolicyRequest(BaseZendeskRequest):
    def put(self, endpoint, help_centre_object, access_policy):
        payload = self.build_payload(access_policy)
        url = self.api._build_url(endpoint(id=help_centre_object))
        return self.api._put(url, payload=payload)

    def delete(self, api_objects, *args, **kwargs):
        raise NotImplementedError("Cannot delete access policies!")

    def post(self, api_objects, *args, **kwargs):
        raise NotImplementedError("POST not supported for access policies!")

    def build_payload(self, help_centre_object):
        return {get_object_type(help_centre_object): self.api._serialize(help_centre_object)}


class TranslationRequest(HelpCentreRequest):
    def build_payload(self, translation):
        return {get_object_type(translation): self.api._serialize(translation)}

    def put(self, endpoint, help_centre_object_id, translation):
        if translation.locale is None:
            raise ZenpyException("Locale can not be None when updating translation!")
        url = self.api._build_url(endpoint(help_centre_object_id, translation.locale))
        payload = self.build_payload(translation)
        return self.api._put(url, payload=payload)

    def delete(self, endpoint, translation):
        url = self.api._build_url(endpoint(id=translation))
        return self.api._delete(url)


class HelpdeskAttachmentRequest(BaseZendeskRequest):
    def delete(self, endpoint, article_attachment):
        url = self.api._build_url(endpoint(id=article_attachment))
        return self.api._delete(url)

    def put(self, api_objects, *args, **kwargs):
        raise NotImplementedError("You cannot update HelpCentre attachments!")

    def post(self, endpoint, attachment, article=None, inline=False):
        if article:
            url = self.api._build_url(endpoint(id=article))
        else:
            url = self.api._build_url(endpoint())

        if hasattr(attachment, 'read'):
            return self.api._post(url, payload={}, files=dict(file=attachment))
        elif os.path.isfile(attachment):
            with open(attachment, 'rb') as fp:
                return self.api._post(url, payload={}, files=dict(file=fp))
        raise ValueError("Attachment is not a file-like object or valid path!")
