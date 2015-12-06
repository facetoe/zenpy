from datetime import datetime, timedelta

__author__ = 'facetoe'

import logging

log = logging.getLogger(__name__)


class ResultGenerator(object):
    """
    Generator for handling pagination.
    """

    # TODO fix this
    endpoint_mapping = {
        'user': 'users',
        'ticket': 'tickets',
        'group': 'groups',
        'results': 'results',
        'organization': 'organizations',
        'topic': 'topics',
        'comment': 'comments',
        'ticket_event': 'ticket_events',
        'ticket_audit': 'audits',
        'tag': 'tags',
        'suspended_ticket': 'suspended_tickets',
        'satisfaction_rating': 'satisfaction_ratings',
        'activity': 'activities',
        'group_membership': 'group_memberships',
        'ticket_metric': 'ticket_metrics',
        'request': 'requests',
        'user_field': 'user_fields',
        'organization_field': 'organization_fields',
        'brand': 'brands',
        'ticket_field': 'ticket_fields'
    }

    def __init__(self, api, result_key, _json):
        self.api = api
        self._json = _json
        self.result_key = self.endpoint_mapping[result_key]
        self.values = _json[self.result_key]
        self.position = 0
        self.update_attrs(self._json)

    def __iter__(self):
        return self

    def __len__(self):
        return self.count

    def __next__(self):
        return self.next()

    def next(self):
        # Pagination
        if self.position >= len(self.values):
            # If we are calling an incremental API, make sure to honour the restrictions
            if 'end_time' in self._json and self._json['end_time']:

                # I'm not sure if this is being handled correctly. If we simply continue iterating
                # while there are still items we end up in an infinite loop that returns the same item
                # over and over again.
                # If we stop iteration when the end_time is equal to the previous end_time we occasionally
                # stop prematurely when a very high number of tickets was created for that instant.
                if self.end_time == self._json['end_time'] and self._json['count'] <= 1:
                    raise StopIteration

                # Update end_time etc
                self.update_attrs(self._json)

                # We can't request updates from an incremental api if the
                # start_time value is less than 5 minutes in the future.
                # (end_time is added as start_time to the next_page URL)
                if (datetime.fromtimestamp(int(self._json['end_time'])) + timedelta(minutes=5)) > datetime.now():
                    raise StopIteration

            if self._json.get('next_page'):
                self._json = self._get_as_json(self._json.get('next_page'))
                self.values = self._json[self.result_key]
                self.position = 0
            else:
                raise StopIteration()

        if not self.values:
            raise StopIteration()

        item_json = self.values[self.position]
        self.position += 1
        if 'result_type' in item_json:
            object_type = item_json.pop('result_type')
        else:
            # Multiple results have a plural key, however the object_type is singular
            object_type = self.get_singular(self.result_key)
        return self.api.object_manager.object_from_json(object_type, item_json)

    def update_attrs(self, _json):
        # Add attributes such as count/end_time that can be present
        for key, value in _json.items():
            if key != self.result_key:
                setattr(self, key, value)

    def _get_as_json(self, url):
        log.debug("GENERATOR: " + url)
        response = self.api._get(url)
        return response.json()

    def get_singular(self, result_key):
        if result_key.endswith('ies'):
            object_type = result_key.replace('ies', 'y')
        else:
            object_type = result_key[:-1]
        return object_type
