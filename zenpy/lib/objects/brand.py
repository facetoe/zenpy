import dateutil.parser

from zenpy.lib.objects.base_object import BaseObject


class Brand(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.default = None
        self.name = None
        self.url = None
        self.created_at = None
        self.updated_at = None
        self.active = None
        self.brand_url = None
        self._logo = None
        self.help_center_state = None
        self.has_help_center = None
        self.subdomain = None
        self.id = None
        self.host_mapping = None

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    @property
    def created(self):
        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, created):
        if created:
            self.created_at = created_at

    @property
    def updated(self):
        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated_at

    @property
    def logo(self):
        if self.api and self._logo:
            return self.api.get_logo(self._logo)

    @logo.setter
    def logo(self, logo):
        if logo:
            self._logo = logo
