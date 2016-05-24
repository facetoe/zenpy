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
        'ticket_metric_events': 'ticket_metric_events',
        'request': 'requests',
        'user_field': 'user_fields',
        'organization_field': 'organization_fields',
        'brand': 'brands',
        'ticket_field': 'ticket_fields',
        'organization_membership': 'organization_memberships',
        'organization_memberships': 'organization_memberships'
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
        # Update end_time etc
        self.update_attrs(self._json)

        # Pagination
        if self.position >= len(self.values):
            end_time = self._json.get('end_time', None)
            next_page = self._json.get('next_page', None)

            # If we are calling an incremental API, make sure to honour the restrictions
            if end_time:
                # Incremental APIs return values in blocks of 1000 and the count value is
                # decremented by 1000 for each block that is consumed. If we have < 1000
                # then there is nothing left to retrieve.
                if self._json.get('count', 0) < 1000:
                    raise StopIteration

                # We can't request updates from an incremental api if the
                # start_time value is less than 5 minutes in the future.
                # (end_time is added as start_time to the next_page URL)
                if (datetime.fromtimestamp(int(end_time)) + timedelta(minutes=5)) > datetime.now():
                    raise StopIteration

            if next_page:
                self._json = self._get_as_json(next_page)
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
