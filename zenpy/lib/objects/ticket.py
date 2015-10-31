import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Ticket(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self._via = None
        self.updated_at = None
        self.submitter_id = None
        self.assignee_id = None
        self.brand_id = None
        self.id = None
        self._custom_fields = None
        self._subject = None
        self.sharing_agreement_ids = None
        self.collaborator_ids = None
        self._priority = None
        self._satisfaction_rating = None
        self._type = None
        self._status = None
        self._description = None
        self.tags = None
        self.forum_topic_id = None
        self.organization_id = None
        self.due_at = None
        self.requester_id = None
        self._recipient = None
        self.problem_id = None
        self._url = None
        self._fields = None
        self.created_at = None
        self._raw_subject = None
        self.has_incidents = None
        self.group_id = None
        self.external_id = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def via(self):
        if self.api and self._via:
            return self.api.get_via(self._via)

    @via.setter
    def via(self, via):
        if via:
            self._via = via

    @property
    def submitter(self):
        if self.api and self.submitter_id:
            return self.api.get_user(self.submitter_id)

    @submitter.setter
    def submitter(self, submitter):
        if submitter:
            self.submitter_id = submitter.id

    @property
    def assignee(self):
        if self.api and self.assignee_id:
            return self.api.get_user(self.assignee_id)

    @assignee.setter
    def assignee(self, assignee):
        if assignee:
            self.assignee_id = assignee.id

    @property
    def brand(self):
        if self.api and self.brand_id:
            return self.api.get_brand(self.brand_id)

    @brand.setter
    def brand(self, brand):
        if brand:
            self.brand_id = brand.id

    @property
    def sharing_agreements(self):
        if self.api and self.sharing_agreement_ids:
            return self.api.get_sharing_agreements(self.sharing_agreement_ids)

    @sharing_agreements.setter
    def sharing_agreements(self, sharing_agreements):
        if sharing_agreements:
            self.sharing_agreement_ids = [o.id for o in sharing_agreements]

    @property
    def collaborators(self):
        if self.api and self.collaborator_ids:
            return self.api.get_users(self.collaborator_ids)

    @collaborators.setter
    def collaborators(self, collaborators):
        if collaborators:
            self.collaborator_ids = [o.id for o in collaborators]

    @property
    def satisfaction_rating(self):
        if self.api and self._satisfaction_rating:
            return self.api.get_satisfaction_rating(self._satisfaction_rating)

    @satisfaction_rating.setter
    def satisfaction_rating(self, satisfaction_rating):
        if satisfaction_rating:
            self._satisfaction_rating = satisfaction_rating

    @property
    def forum_topic(self):
        if self.api and self.forum_topic_id:
            return self.api.get_topic(self.forum_topic_id)

    @forum_topic.setter
    def forum_topic(self, forum_topic):
        if forum_topic:
            self.forum_topic_id = forum_topic.id

    @property
    def organization(self):
        if self.api and self.organization_id:
            return self.api.get_organization(self.organization_id)

    @organization.setter
    def organization(self, organization):
        if organization:
            self.organization_id = organization.id

    @property
    def requester(self):
        if self.api and self.requester_id:
            return self.api.get_user(self.requester_id)

    @requester.setter
    def requester(self, requester):
        if requester:
            self.requester_id = requester.id

    @property
    def problem(self):
        if self.api and self.problem_id:
            return self.api.get_problem(self.problem_id)

    @problem.setter
    def problem(self, problem):
        if problem:
            self.problem_id = problem.id

    @property
    def group(self):
        if self.api and self.group_id:
            return self.api.get_group(self.group_id)

    @group.setter
    def group(self, group):
        if group:
            self.group_id = group.id

    @property
    def external(self):
        if self.api and self.external_id:
            return self.api.get_external(self.external_id)

    @external.setter
    def external(self, external):
        if external:
            self.external_id = external.id
