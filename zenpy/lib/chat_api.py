from zenpy.lib.api import Api
from zenpy.lib.mapping import ChatObjectMapping
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

    def __init__(self, config, endpoint, request_handler=None):
        super(ChatApiBase, self).__init__(config,
                                          object_type='chat',
                                          endpoint=endpoint)
        self._request_handler = request_handler or ChatApiRequest
        self._object_manager = ChatObjectMapping(self)
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
    def __init__(self, config, endpoint):
        super(AgentApi, self).__init__(config,
                                       endpoint=endpoint,
                                       request_handler=AgentRequest)

    def me(self):
        return self._get(self._build_url(self.endpoint.me()))


class ChatApi(ChatApiBase):
    def __init__(self, config, endpoint):
        super(ChatApi, self).__init__(config, endpoint=endpoint)

        self.accounts = ChatApiBase(config, endpoint.account, request_handler=AccountRequest)

        self.agents = AgentApi(config, endpoint.agents)

        self.visitors = ChatApiBase(config, endpoint.visitors, request_handler=VisitorRequest)

        self.shortcuts = ChatApiBase(config, endpoint.shortcuts)

        self.triggers = ChatApiBase(config, endpoint.triggers)

        self.bans = ChatApiBase(config, endpoint.bans)

        self.departments = ChatApiBase(config, endpoint.departments)

        self.goals = ChatApiBase(config, endpoint.goals)

        self.stream = ChatApiBase(config, endpoint.stream)

    def search(self, *args, **kwargs):
        url = self._build_url(self.endpoint.search(*args, **kwargs))
        return self._get(url)
