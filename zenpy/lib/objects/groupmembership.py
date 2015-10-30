import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class GroupMembership(BaseObject):
    def __init__(self, api=None):
        self.api = api
        self._user = None
        self.user_id = None
        self.url = None
        self._created = None
        self.created_at = None
        self._updated = None
        self.updated_at = None
        self.default = None
        self._group = None
        self.group_id = None
        self.id = None

    @property
    def user(self):
        if self.api and self.user_id:
            return self.api.get_user(self.user_id)

    @user.setter
    def user(self, value):
        self._user = value

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, value):
        self._created = value

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, value):
        self._updated = value

    @property
    def group(self):
        if self.api and self.group_id:
            return self.api.get_group(self.group_id)

    @group.setter
    def group(self, value):
        self._group = value
