from zenpy.lib.api_objects import BaseObject
import dateutil.parser


class Account(BaseObject):
    def __init__(self,
                 api=None,
                 account_key=None,
                 billing=None,
                 create_date=None,
                 plan=None,
                 status=None,
                 **kwargs):

        self.api = api
        self.account_key = account_key
        self.billing = billing
        self.create_date = create_date
        self.plan = plan
        self.status = status

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Agent(BaseObject):
    def __init__(self,
                 api=None,
                 create_date=None,
                 departments=None,
                 display_name=None,
                 email=None,
                 enabled=None,
                 first_name=None,
                 id=None,
                 last_login=None,
                 last_name=None,
                 login_count=None,
                 roles=None,
                 **kwargs):

        self.api = api
        self.create_date = create_date
        self.departments = departments
        self.display_name = display_name
        self.email = email
        self.enabled = enabled
        self.first_name = first_name
        self.id = id
        self.last_login = last_login
        self.last_name = last_name
        self.login_count = login_count
        self.roles = roles

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Ban(BaseObject):
    def __init__(self, api=None, ip_address=None, visitor=None, **kwargs):

        self.api = api
        self.ip_address = ip_address
        self.visitor = visitor

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Billing(BaseObject):
    def __init__(self,
                 api=None,
                 additional_info=None,
                 address1=None,
                 address2=None,
                 city=None,
                 company=None,
                 country_code=None,
                 email=None,
                 first_name=None,
                 last_name=None,
                 postal_code=None,
                 state=None,
                 **kwargs):

        self.api = api
        self.additional_info = additional_info
        self.address1 = address1
        self.address2 = address2
        self.city = city
        self.company = company
        self.country_code = country_code
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.postal_code = postal_code
        self.state = state

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Chat(BaseObject):
    def __init__(self,
                 api=None,
                 agent_ids=None,
                 agent_names=None,
                 comment=None,
                 count=None,
                 department_id=None,
                 department_name=None,
                 duration=None,
                 history=None,
                 id=None,
                 missed=None,
                 rating=None,
                 referrer_search_engine=None,
                 referrer_search_terms=None,
                 response_time=None,
                 session=None,
                 started_by=None,
                 tags=None,
                 triggered=None,
                 triggered_response=None,
                 type=None,
                 unread=None,
                 visitor=None,
                 webpath=None,
                 zendesk_ticket_id=None,
                 **kwargs):

        self.api = api

        self._end_timestamp = None

        self._timestamp = None
        self.agent_ids = agent_ids
        self.agent_names = agent_names
        self.comment = comment
        self.count = count
        self.department_id = department_id
        self.department_name = department_name
        self.duration = duration
        self.history = history
        self.id = id
        self.missed = missed
        self.rating = rating
        self.referrer_search_engine = referrer_search_engine
        self.referrer_search_terms = referrer_search_terms
        self.response_time = response_time
        self.session = session
        self.started_by = started_by
        self.tags = tags
        self.triggered = triggered
        self.triggered_response = triggered_response
        self.type = type
        self.unread = unread
        self.visitor = visitor
        self.webpath = webpath
        self.zendesk_ticket_id = zendesk_ticket_id

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

    @property
    def end_timestamp(self):

        if self._end_timestamp:
            return dateutil.parser.parse(self._end_timestamp)

    @end_timestamp.setter
    def end_timestamp(self, end_timestamp):
        if end_timestamp:
            self._end_timestamp = end_timestamp

    @property
    def timestamp(self):

        if self._timestamp:
            return dateutil.parser.parse(self._timestamp)

    @timestamp.setter
    def timestamp(self, timestamp):
        if timestamp:
            self._timestamp = timestamp

    @property
    def agents(self):

        if self.api and self.agent_ids:
            return self.api._get_agents(self.agent_ids)

    @agents.setter
    def agents(self, agents):
        if agents:
            self.agent_ids = [o.id for o in agents]
            self._agents = agents

    @property
    def department(self):

        if self.api and self.department_id:
            return self.api._get_department(self.department_id)

    @department.setter
    def department(self, department):
        if department:
            self.department_id = department.id
            self._department = department

    @property
    def zendesk_ticket(self):

        if self.api and self.zendesk_ticket_id:
            return self.api._get_zendesk_ticket(self.zendesk_ticket_id)

    @zendesk_ticket.setter
    def zendesk_ticket(self, zendesk_ticket):
        if zendesk_ticket:
            self.zendesk_ticket_id = zendesk_ticket.id
            self._zendesk_ticket = zendesk_ticket


class Count(BaseObject):
    def __init__(self,
                 api=None,
                 agent=None,
                 total=None,
                 visitor=None,
                 **kwargs):

        self.api = api
        self.agent = agent
        self.total = total
        self.visitor = visitor

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Definition(BaseObject):
    def __init__(self,
                 api=None,
                 actions=None,
                 condition=None,
                 event=None,
                 **kwargs):

        self.api = api
        self.actions = actions
        self.condition = condition
        self.event = event

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Department(BaseObject):
    def __init__(self,
                 api=None,
                 description=None,
                 enabled=None,
                 id=None,
                 members=None,
                 name=None,
                 settings=None,
                 **kwargs):

        self.api = api
        self.description = description
        self.enabled = enabled
        self.id = id
        self.members = members
        self.name = name
        self.settings = settings

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Goal(BaseObject):
    def __init__(self,
                 api=None,
                 attribution_model=None,
                 attribution_period=None,
                 description=None,
                 enabled=None,
                 id=None,
                 name=None,
                 settings=None,
                 **kwargs):

        self.api = api
        self.attribution_model = attribution_model
        self.attribution_period = attribution_period
        self.description = description
        self.enabled = enabled
        self.id = id
        self.name = name
        self.settings = settings

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class IpAddress(BaseObject):
    def __init__(self,
                 api=None,
                 id=None,
                 ip_address=None,
                 reason=None,
                 type=None,
                 **kwargs):

        self.api = api
        self.id = id
        self.ip_address = ip_address
        self.reason = reason
        self.type = type

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class OfflineMessage(BaseObject):
    def __init__(self,
                 api=None,
                 department_id=None,
                 department_name=None,
                 id=None,
                 message=None,
                 session=None,
                 type=None,
                 unread=None,
                 visitor=None,
                 zendesk_ticket_id=None,
                 **kwargs):

        self.api = api

        self._timestamp = None
        self.department_id = department_id
        self.department_name = department_name
        self.id = id
        self.message = message
        self.session = session
        self.type = type
        self.unread = unread
        self.visitor = visitor
        self.zendesk_ticket_id = zendesk_ticket_id

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

    @property
    def timestamp(self):

        if self._timestamp:
            return dateutil.parser.parse(self._timestamp)

    @timestamp.setter
    def timestamp(self, timestamp):
        if timestamp:
            self._timestamp = timestamp

    @property
    def department(self):

        if self.api and self.department_id:
            return self.api._get_department(self.department_id)

    @department.setter
    def department(self, department):
        if department:
            self.department_id = department.id
            self._department = department

    @property
    def zendesk_ticket(self):

        if self.api and self.zendesk_ticket_id:
            return self.api._get_zendesk_ticket(self.zendesk_ticket_id)

    @zendesk_ticket.setter
    def zendesk_ticket(self, zendesk_ticket):
        if zendesk_ticket:
            self.zendesk_ticket_id = zendesk_ticket.id
            self._zendesk_ticket = zendesk_ticket


class Plan(BaseObject):
    def __init__(self,
                 api=None,
                 agent_leaderboard=None,
                 agent_reports=None,
                 analytics=None,
                 chat_reports=None,
                 daily_reports=None,
                 email_reports=None,
                 file_upload=None,
                 goals=None,
                 high_load=None,
                 integrations=None,
                 ip_restriction=None,
                 long_desc=None,
                 max_advanced_triggers=None,
                 max_agents=None,
                 max_basic_triggers=None,
                 max_concurrent_chats=None,
                 max_departments=None,
                 max_history_search_days=None,
                 monitoring=None,
                 name=None,
                 operating_hours=None,
                 price=None,
                 rest_api=None,
                 short_desc=None,
                 sla=None,
                 support=None,
                 unbranding=None,
                 widget_customization=None,
                 **kwargs):

        self.api = api
        self.agent_leaderboard = agent_leaderboard
        self.agent_reports = agent_reports
        self.analytics = analytics
        self.chat_reports = chat_reports
        self.daily_reports = daily_reports
        self.email_reports = email_reports
        self.file_upload = file_upload
        self.goals = goals
        self.high_load = high_load
        self.integrations = integrations
        self.ip_restriction = ip_restriction
        self.long_desc = long_desc
        self.max_advanced_triggers = max_advanced_triggers
        self.max_agents = max_agents
        self.max_basic_triggers = max_basic_triggers
        self.max_concurrent_chats = max_concurrent_chats
        self.max_departments = max_departments
        self.max_history_search_days = max_history_search_days
        self.monitoring = monitoring
        self.name = name
        self.operating_hours = operating_hours
        self.price = price
        self.rest_api = rest_api
        self.short_desc = short_desc
        self.sla = sla
        self.support = support
        self.unbranding = unbranding
        self.widget_customization = widget_customization

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class ResponseTime(BaseObject):
    def __init__(self, api=None, avg=None, first=None, max=None, **kwargs):

        self.api = api
        self.avg = avg
        self.first = first
        self.max = max

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Roles(BaseObject):
    def __init__(self, api=None, administrator=None, owner=None, **kwargs):

        self.api = api
        self.administrator = administrator
        self.owner = owner

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class SearchResult(BaseObject):
    def __init__(self,
                 api=None,
                 id=None,
                 preview=None,
                 type=None,
                 url=None,
                 **kwargs):

        self.api = api

        self._timestamp = None
        self.id = id
        self.preview = preview
        self.type = type
        self.url = url

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

    @property
    def timestamp(self):

        if self._timestamp:
            return dateutil.parser.parse(self._timestamp)

    @timestamp.setter
    def timestamp(self, timestamp):
        if timestamp:
            self._timestamp = timestamp


class Session(BaseObject):
    def __init__(self,
                 api=None,
                 browser=None,
                 city=None,
                 country_code=None,
                 country_name=None,
                 end_date=None,
                 id=None,
                 ip=None,
                 platform=None,
                 region=None,
                 start_date=None,
                 user_agent=None,
                 **kwargs):

        self.api = api
        self.browser = browser
        self.city = city
        self.country_code = country_code
        self.country_name = country_name
        self.end_date = end_date

        # Comment: Automatically assigned when the session is created
        # Mandatory: yes
        # Read-only: yes
        # Type: integer
        self.id = id
        self.ip = ip
        self.platform = platform
        self.region = region
        self.start_date = start_date
        self.user_agent = user_agent

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Shortcut(BaseObject):
    def __init__(self,
                 api=None,
                 message=None,
                 name=None,
                 options=None,
                 tags=None,
                 **kwargs):

        self.api = api
        self.message = message
        self.name = name
        self.options = options
        self.tags = tags

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Trigger(BaseObject):
    def __init__(self,
                 api=None,
                 definition=None,
                 description=None,
                 enabled=None,
                 name=None,
                 **kwargs):

        self.api = api
        self.definition = definition
        self.description = description
        self.enabled = enabled
        self.name = name

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Visitor(BaseObject):
    def __init__(self,
                 api=None,
                 email=None,
                 id=None,
                 name=None,
                 notes=None,
                 phone=None,
                 **kwargs):

        self.api = api
        self.email = email
        self.id = id
        self.name = name
        self.notes = notes
        self.phone = phone

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue


class Webpath(BaseObject):
    def __init__(self, api=None, from_=None, title=None, to=None, **kwargs):

        self.api = api

        self._timestamp = None
        self.from_ = from_
        self.title = title
        self.to = to

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

    @property
    def timestamp(self):

        if self._timestamp:
            return dateutil.parser.parse(self._timestamp)

    @timestamp.setter
    def timestamp(self, timestamp):
        if timestamp:
            self._timestamp = timestamp
