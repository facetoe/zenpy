from zenpy.lib.objects.base_object import BaseObject


class GroupMembership(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.user_id = None
        self._url = None
        self.created_at = None
        self.updated_at = None
        self.default = None
        self.group_id = None
        self.id = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def user(self):
        if self.api and self.user_id:
            return self.api.get_user(self.user_id)

    @user.setter
    def user(self, user):
        if user:
            self.user_id = user.id

    @property
    def group(self):
        if self.api and self.group_id:
            return self.api.get_group(self.group_id)

    @group.setter
    def group(self, group):
        if group:
            self.group_id = group.id
