from zenpy.lib.api_objects import BaseObject


class Integration(BaseObject):
    """
    ######################################################################
    #    Do not modify, this class is autogenerated by gen_classes.py    #
    ######################################################################
    """

    def __init__(self,
                 api=None,
                 description=None,
                 jwt_public_key=None,
                 zendesk_oauth_client=None,
                 **kwargs):

        self.api = api
        self.description = description
        self.jwt_public_key = jwt_public_key
        self.zendesk_oauth_client = zendesk_oauth_client

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue
