import collections

from zenpy.lib.api import Api
from zenpy.lib.deserializer import ChatDeserializer
from zenpy.lib.request import AccountRequest
from zenpy.lib.api_objects.chat_objects import Shortcut, Trigger
from zenpy.lib.response import ChatResponseHandler, AccountResponseHandler


class ChatApiBase(Api):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit, response_handlers=None):
        super(Api, self).__init__(subdomain, session, endpoint,
                                            timeout=timeout,
                                            ratelimit=ratelimit,
                                            object_type='chat')  # TODO: figure out what to do with object_type
        self._deserializer = ChatDeserializer(self)
        self._url_template = "%(protocol)s://www.zopim.com/%(api_prefix)s"
        self._response_handlers = response_handlers or (ChatResponseHandler,)

    # def update(self, chat_object):
    #     payload = self._build_update_payload(chat_object)
    #     identifier = self._get_chat_object_identifier(chat_object)
    #     return self._do(self._put,
    #                     endpoint=self.endpoint,
    #                     endpoint_kwargs={identifier: getattr(chat_object, identifier)},
    #                     payload=payload)
    #
    # def create(self, chat_object):
    #     payload = self._build_payload(chat_object)
    #     return self._do(self._post,
    #                     endpoint=self.endpoint,
    #                     payload=payload)
    #
    # def delete(self, chat_object):
    #     self._check_type(chat_object)
    #     identifier = self._get_chat_object_identifier(chat_object)
    #     return self._do(self._delete, endpoint_kwargs={identifier: getattr(chat_object, identifier)})
    #
    # def _get_chat_object_identifier(self, chat_object):
    #     identifier = 'id'
    #     for chat_type in (Shortcut, Trigger):
    #         if isinstance(chat_object, chat_type):
    #             identifier = 'name'
    #     return identifier
    #
    # def _build_update_payload(self, chat_objects):
    #     self._check_type(chat_objects)
    #     return self._flatten_chat_object(self._serialize(chat_objects))
    #
    # def _build_payload(self, chat_objects):
    #     self._check_type(chat_objects)
    #     return self._serialize(chat_objects)
    #
    # def _flatten_chat_object(self, chat_object, parent_key=''):
    #     items = []
    #     for key, value in chat_object.items():
    #         new_key = "{}.{}".format(parent_key, key) if parent_key else key
    #         if isinstance(value, collections.MutableMapping):
    #             items.extend(self._flatten_chat_object(value, new_key).items())
    #         else:
    #             items.append((new_key, value))
    #     return dict(items)
    #
    # def _get_webpath(self, webpaths):
    #     for webpath in webpaths:
    #         yield self._deserializer.object_from_json('webpath', webpath)


class AccountApi(ChatApiBase):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        super(AccountApi, self).__init__(subdomain, session, endpoint,
                                         timeout=timeout,
                                         ratelimit=ratelimit, response_handlers=(AccountResponseHandler,))

    def update(self, chat_object):
        return AccountRequest(self).perform("PUT", chat_object)


class ChatApi(ChatApiBase):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        super(ChatApi, self).__init__(subdomain, session, endpoint,
                                      timeout=timeout,
                                      ratelimit=ratelimit)
        self.account = AccountApi(subdomain, session, endpoint.account, timeout, ratelimit)
