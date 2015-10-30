import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Ticket(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.via = None
        self.updated_at = None
        self._submitter = None
        self.submitter_id = None
        self._assignee = None
        self.assignee_id = None
        self._brand = None
        self.brand_id = None
        self.id = None
        self.custom_fields = None
        self.subject = None
        self.sharing_agreement_ids = None
        self.collaborator_ids = None
        self.priority = None
        self.satisfaction_rating = None
        self.type = None
        self.status = None
        self.description = None
        self.tags = None
        self._forum_topic = None
        self.forum_topic_id = None
        self._organization = None
        self.organization_id = None
        self.due_at = None
        self._requester = None
        self.requester_id = None
        self.recipient = None
        self._problem = None
        self.problem_id = None
        self.url = None
        self.fields = None
        self.created_at = None
        self.raw_subject = None
        self.has_incidents = None
        self._group = None
        self.group_id = None
        self._external = None
        self.external_id = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, value):
        self._updated = value

    @property
    def submitter(self):
        if self.api and self.submitter_id:
            return self.api.get_user(self.submitter_id)

    @submitter.setter
    def submitter(self, user):
        self.submitter_id = user.id

    @property
    def assignee(self):
        if self.api and self.assignee_id:
            return self.api.get_user(self.assignee_id)

    @assignee.setter
    def assignee(self, user):
        self.assignee_id = user.id

    @property
    def brand(self):
        if self.api and self.brand_id:
            return self.api.get_brand(self.brand_id)

    @brand.setter
    def brand(self, brand):
        self.brand_id = brand.id

    @property
    def forum_topic(self):
        if self.api and self.forum_topic_id:
            return self.api.get_topic(self.forum_topic_id)

    @forum_topic.setter
    def forum_topic(self, forum_topic):
        self.forum_topic_id = forum_topic.id

    @property
    def organization(self):
        if self.api and self.organization_id:
            return self.api.get_organization(self.organization_id)

    @organization.setter
    def organization(self, organization):
        self.organization_id = organization.id

    @property
    def due(self):
        if self.due_at:
            return dateutil.parser.parse(self.due_at)

    @due.setter
    def due(self, value):
        self._due = value

    @property
    def requester(self):
        if self.api and self.requester_id:
            return self.api.get_user(self.requester_id)

    @requester.setter
    def requester(self, user):
        self.requester_id = user.id

    @property
    def problem(self):
        if self.api and self.problem_id:
            return self.api.get_problem(self.problem_id)

    @problem.setter
    def problem(self, problem):
        self.problem_id = problem.id

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, value):
        self._created = value

    @property
    def group(self):
        if self.api and self.group_id:
            return self.api.get_group(self.group_id)

    @group.setter
    def group(self, group):
        self.group_id = group.id

    @property
    def external(self):
        if self.api and self.external_id:
            return self.api.get_external(self.external_id)

    @external.setter
    def external(self, external):
        self.external_id = external.id
