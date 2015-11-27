from zenpy.lib.objects.base_object import BaseObject


class TicketSharingEvent(BaseObject):
    def __init__(self, api=None, **kwargs):
        self.api = api
        self.agreement_id = None
        self.action = None
        self.type = None
        self.id = None

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def agreement(self):
        if self.api and self.agreement_id:
            return self.api.get_agreement(self.agreement_id)

    @agreement.setter
    def agreement(self, agreement):
        if agreement:
            self.agreement_id = agreement.id
