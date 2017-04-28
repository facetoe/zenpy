from zenpy.lib.api import Api
from zenpy.lib.object_manager import ChatObjectManager
from zenpy.lib.request import (
    AccountRequest,
    AgentRequest,
    ChatApiRequest,
    VisitorRequest
)
from zenpy.lib.response import (
    ChatResponseHandler,
    AccountResponseHandler,
    AgentResponseHandler,
    DeleteResponseHandler,
    VisitorResponseHandler,
    ChatSearchResponseHandler,
    ShortcutResponseHandler,
    TriggerResponseHandler,
    BanResponseHandler,
    GoalResponseHandler,
    DepartmentResponseHandler
)


class ChatApiBase(Api):
    """
    Implements most generic ChatApi functionality. Most if the actual work is delegated to 
    Request and Response handlers. 
    """

    def __init__(self, subdomain, session, endpoint, timeout, ratelimit, request_handler=None):
        super(Api, self).__init__(subdomain, session, endpoint,
                                  timeout=timeout,
                                  ratelimit=ratelimit,
                                  object_type='chat')
        self._request_handler = request_handler or ChatApiRequest
        self._object_manager = ChatObjectManager(self)
        self._url_template = "%(protocol)s://www.zopim.com/%(api_prefix)s"
        self._response_handlers = (
            DeleteResponseHandler,
            ChatSearchResponseHandler,
            ChatResponseHandler,
            AccountResponseHandler,
            AgentResponseHandler,
            VisitorResponseHandler,
            ShortcutResponseHandler,
            TriggerResponseHandler,
            BanResponseHandler,
            DepartmentResponseHandler,
            GoalResponseHandler
        )

    def create(self, *args, **kwargs):
        return self._request_handler(self).perform("POST", *args, **kwargs)

    def update(self, *args, **kwargs):
        return self._request_handler(self).perform("PUT", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._request_handler(self).perform("DELETE", *args, **kwargs)

    def _get_ip_address(self, ips):
        for ip in ips:
            yield self._object_manager.object_from_json('ip_address', ip)


class AgentApi(ChatApiBase):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        super(AgentApi, self).__init__(subdomain, session, endpoint,
                                       timeout=timeout,
                                       ratelimit=ratelimit,
                                       request_handler=AgentRequest)

    def me(self):
        return self._get(self._build_url(self.endpoint.me()))


class ChatApi(ChatApiBase):
    def __init__(self, subdomain, session, endpoint, timeout, ratelimit):
        super(ChatApi, self).__init__(subdomain, session, endpoint,
                                      timeout=timeout,
                                      ratelimit=ratelimit)
        self.accounts = ChatApiBase(subdomain, session, endpoint.account, timeout, ratelimit,
                                    request_handler=AccountRequest)
        self.agents = AgentApi(subdomain, session, endpoint.agents, timeout, ratelimit)
        self.visitors = ChatApiBase(subdomain, session, endpoint.visitors, timeout, ratelimit,
                                    request_handler=VisitorRequest)
        self.shortcuts = ChatApiBase(subdomain, session, endpoint.shortcuts, timeout, ratelimit)
        self.triggers = ChatApiBase(subdomain, session, endpoint.triggers, timeout, ratelimit)
        self.bans = ChatApiBase(subdomain, session, endpoint.bans, timeout, ratelimit)
        self.departments = ChatApiBase(subdomain, session, endpoint.departments, timeout, ratelimit)
        self.goals = ChatApiBase(subdomain, session, endpoint.goals, timeout, ratelimit)
        self.stream = ChatApiBase(subdomain, session, endpoint.stream, timeout, ratelimit)

    def search(self, *args, **kwargs):
        url = self._build_url(self.endpoint.search(*args, **kwargs))
        return self._get(url)
