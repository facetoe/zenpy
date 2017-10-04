from zenpy.lib.api_objects import BaseObject
import dateutil.parser


class Article(BaseObject):
    def __init__(self,
                 api=None,
                 author_id=None,
                 body=None,
                 comments_disabled=None,
                 created_at=None,
                 draft=None,
                 html_url=None,
                 id=None,
                 label_names=None,
                 locale=None,
                 name=None,
                 outdated=None,
                 outdated_locales=None,
                 position=None,
                 promoted=None,
                 section_id=None,
                 source_locale=None,
                 title=None,
                 updated_at=None,
                 url=None,
                 vote_count=None,
                 vote_sum=None,
                 **kwargs):

        self.api = api
        self.author_id = author_id
        self.body = body
        self.comments_disabled = comments_disabled
        self.created_at = created_at
        self.draft = draft
        self.html_url = html_url
        self.id = id
        self.label_names = label_names
        self.locale = locale
        self.name = name
        self.outdated = outdated
        self.outdated_locales = outdated_locales
        self.position = position
        self.promoted = promoted
        self.section_id = section_id
        self.source_locale = source_locale
        self.title = title
        self.updated_at = updated_at
        self.url = url
        self.vote_count = vote_count
        self.vote_sum = vote_sum

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def author(self):

        if self.api and self.author_id:
            return self.api._get_user(self.author_id)

    @author.setter
    def author(self, author):
        if author:
            self.author_id = author.id
            self._author = author

    @property
    def created(self):

        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, created):
        if created:
            self.created_at = created

    @property
    def section(self):

        if self.api and self.section_id:
            return self.api._get_section(self.section_id)

    @section.setter
    def section(self, section):
        if section:
            self.section_id = section.id
            self._section = section

    @property
    def updated(self):

        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated


class Category(BaseObject):
    def __init__(self,
                 api=None,
                 created_at=None,
                 description=None,
                 html_url=None,
                 id=None,
                 locale=None,
                 name=None,
                 outdated=None,
                 position=None,
                 source_locale=None,
                 updated_at=None,
                 url=None,
                 **kwargs):

        self.api = api
        self.created_at = created_at
        self.description = description
        self.html_url = html_url
        self.id = id
        self.locale = locale
        self.name = name
        self.outdated = outdated
        self.position = position
        self.source_locale = source_locale
        self.updated_at = updated_at
        self.url = url

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


class Comment(BaseObject):
    def __init__(self,
                 api=None,
                 author_id=None,
                 body=None,
                 created_at=None,
                 html_url=None,
                 id=None,
                 locale=None,
                 source_id=None,
                 source_type=None,
                 updated_at=None,
                 url=None,
                 vote_count=None,
                 vote_sum=None,
                 **kwargs):

        self.api = api
        self.author_id = author_id
        self.body = body
        self.created_at = created_at
        self.html_url = html_url
        self.id = id
        self.locale = locale
        self.source_id = source_id
        self.source_type = source_type
        self.updated_at = updated_at
        self.url = url
        self.vote_count = vote_count
        self.vote_sum = vote_sum

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def author(self):

        if self.api and self.author_id:
            return self.api._get_user(self.author_id)

    @author.setter
    def author(self, author):
        if author:
            self.author_id = author.id
            self._author = author

    @property
    def created(self):

        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, created):
        if created:
            self.created_at = created

    @property
    def source(self):

        if self.api and self.source_id:
            return self.api._get_source(self.source_id)

    @source.setter
    def source(self, source):
        if source:
            self.source_id = source.id
            self._source = source

    @property
    def updated(self):

        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated


class Section(BaseObject):
    def __init__(self,
                 api=None,
                 category_id=None,
                 created_at=None,
                 description=None,
                 html_url=None,
                 id=None,
                 locale=None,
                 manageable_by=None,
                 name=None,
                 outdated=None,
                 position=None,
                 sorting=None,
                 source_locale=None,
                 updated_at=None,
                 url=None,
                 user_segment_id=None,
                 **kwargs):

        self.api = api
        self.category_id = category_id
        self.created_at = created_at
        self.description = description
        self.html_url = html_url
        self.id = id
        self.locale = locale
        self.manageable_by = manageable_by
        self.name = name
        self.outdated = outdated
        self.position = position
        self.sorting = sorting
        self.source_locale = source_locale
        self.updated_at = updated_at
        self.url = url
        self.user_segment_id = user_segment_id

        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def category(self):

        if self.api and self.category_id:
            return self.api._get_category(self.category_id)

    @category.setter
    def category(self, category):
        if category:
            self.category_id = category.id
            self._category = category

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
    def user_segment(self):

        if self.api and self.user_segment_id:
            return self.api._get_user_segment(self.user_segment_id)

    @user_segment.setter
    def user_segment(self, user_segment):
        if user_segment:
            self.user_segment_id = user_segment.id
            self._user_segment = user_segment
