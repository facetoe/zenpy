import json

__author__ = 'facetoe'

import types
import dateutil.parser
import dateutil
import logging
from cStringIO import StringIO

log = logging.getLogger(__name__)


class BaseApiObject(object):
    SINGLE_GENERATORS = (
        'requester',
        'submitter',
        'assignee',
        'group',
        'content',
        'author',
        'photo'
    )

    def __getattribute__(self, name):
        obj = object.__getattribute__(self, name)
        if name.endswith("_at") and obj:
            return dateutil.parser.parse(obj)

        if name in object.__getattribute__(self, 'SINGLE_GENERATORS'):
            if isinstance(obj, ApiCallGenerator) or isinstance(obj, types.GeneratorType):
                return obj.next()

        if isinstance(obj, list):
            if all([isinstance(o, dict) for o in obj]):
                return self.handle_dicts(obj)
        elif isinstance(obj, dict):
            class_name = self.api.get_class_name_from_json(obj)
            return ApiClassFactory(class_name, obj, self.api)

        return object.__getattribute__(self, name)

    def handle_dicts(self, dicts):
        for item in dicts:
            class_name = self.api.get_class_name_from_json(item)
            yield ApiClassFactory(class_name, item, self.api)

    def is_ticket(self):
        return self.__name__ == 'Ticket'

    def is_user(self):
        return self.__name__ == 'User'

    def is_group(self):
        return self.__name__ == 'Group'

    def is_comment(self):
        return self.__name__ == 'Comment'

    def is_attachment(self):
        return self.__name__ == 'Attachment'

    def __repr__(self):
        if self.is_user():
            return str(self.name)
        elif self.is_group():
            return self.name
        elif self.is_ticket():
            return self.id
        elif self.is_attachment():
            return self.file_name
        else:
            return self.__name__.lower()


class ApiCallGenerator(object):
    api = None
    request_json = None
    position = 0
    values = list()
    multiple_results = ('tickets', 'users', 'groups', 'results', 'comments')
    single_results = ('ticket', 'user', 'group',)

    def __init__(self, api, request_json):
        self.api = api
        self.request_json = request_json
        self.values = self.get_values(request_json)

    def get_values(self, request_json):
        values = list()
        for result_type in self.multiple_results:
            if result_type in request_json:
                values = values + request_json[result_type]
        for result_type in self.single_results:
            if result_type in request_json:
                values.append(request_json[result_type])
        return values

    def __iter__(self):
        return self

    # Python 3 compatibility
    def __next__(self):
        return self.next()

    def make_request(self, url):
        log.info("Making generator request to: " + url)
        response = self.api.raw_request(url)
        return response.json()

    def next(self):
        # Pagination
        if self.position >= len(self.values):
            if self.request_json.get('next_page'):
                self.request_json = self.make_request(self.request_json.get('next_page'))
                self.values = self.get_values(self.request_json)
                self.position = 0
            else:
                raise StopIteration()

        if not self.values:
            raise StopIteration()

        item_json = self.values[self.position]
        self.position += 1
        class_name = self.api.get_class_name_from_json(item_json)
        return ApiClassFactory(class_name, item_json, self.api)


def ApiClassFactory(name, member_dict, api, BaseClass=BaseApiObject):
    def __init__(self, **kwargs):
        setattr(self, 'api', api)
        setattr(self, '__name__', name)
        for key, value in kwargs.items():
            setattr(self, key, value)
        BaseClass.__init__(self)

    def get_items(item_ids, endpoint):
        if item_ids is None:
            return None

        if isinstance(item_ids, int):
            item_id = item_ids
            if item_id in api.object_cache.keys():
                return api.object_cache[item_id]
            else:
                url = api.get_url(endpoint(id=item_id))

        elif isinstance(item_ids, list):
            if all([item_id in api.object_cache.keys() for item_id in item_ids]):
                return [api.object_cache[item_id] for item_id in item_ids]
            else:
                url = api.get_url(endpoint(ids=item_ids))
        else:
            raise Exception("Unknown type passed to get_items(): " + str(item_ids))

        # This is a bit hacky, pass the url to next_page so the api call won't be made until
        # the item is requested
        request_json = dict(next_page=url)
        return ApiCallGenerator(api, request_json)

    def get_attachment_content():
        yield download_file(member_dict['content_url'])

    def download_file(url):
        response = api.raw_request(url, stream=True)
        outfile = StringIO()
        for chunk in response.iter_content():
            outfile.write(chunk)
        file_contents = outfile.getvalue()
        outfile.close()
        return file_contents

    def populate_ticket():
        for user_type in ('submitter_id', 'requester_id', 'assignee_id', 'collaborator_ids'):
            item = get_items(member_dict[user_type], api.endpoint.users)
            setattr(api_object, user_type.replace('_id', ''), item)

        group = get_items(member_dict['group_id'], api.endpoint.groups)
        setattr(api_object, 'group', group)

        comments = get_items(member_dict['id'], api.endpoint.comments)
        setattr(api_object, 'comments', comments)

    def populate_attachment():
        content = get_attachment_content()
        setattr(api_object, 'content', content)

    def populate_comment():
        author = get_items(member_dict['author_id'], api.endpoint.users)
        setattr(api_object, 'author', author)

    api_object = type(name, (BaseClass,), {"__init__": __init__})(**member_dict)
    if api_object.is_ticket():
        populate_ticket()
    else:
        if api_object.id not in api.object_cache.keys():
            log.debug("Adding object to cache: " + str(api_object))
            api.object_cache.update({api_object.id: api_object})
        else:
            log.debug("Object in cache: " + str(api_object.id))

        if api_object.is_attachment():
            populate_attachment()
        elif api_object.is_comment():
            populate_comment()

    return api_object
