import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Forum(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.access = None
        self.locked = None
        self.description = None
        self.tags = None
        self.url = None
        self.created_at = None
        self.forum_type = None
        self.updated_at = None
        self.locale_id = None
        self.organization_id = None
        self.position = None
        self.category_id = None
        self.id = None
        self.name = None

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, created):
        if created:
            self.created_at = created

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated

    @property
    def organization(self):
        if self.api and self.organization_id:
            return self.api.get_organization(self.organization_id)

    @organization.setter
    def organization(self, organization):
        if organization:
            self.organization_id = organization.id

    @property
    def category(self):
        if self.api and self.category_id:
            return self.api.get_category(self.category_id)

    @category.setter
    def category(self, category):
        if category:
            self.category_id = category.id
