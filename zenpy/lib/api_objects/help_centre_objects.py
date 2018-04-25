from zenpy.lib.api_objects import BaseObject
import dateutil.parser


class AccessPolicy(BaseObject):
    def __init__(self,
                 api=None,
                 manageable_by=None,
                 required_tags=None,
                 restricted_to_group_ids=None,
                 restricted_to_organization_ids=None,
                 viewable_by=None,
                 **kwargs):

        self.api = api
        self.manageable_by = manageable_by
        self.required_tags = required_tags
        self.restricted_to_group_ids = restricted_to_group_ids
        self.restricted_to_organization_ids = restricted_to_organization_ids
        self.viewable_by = viewable_by

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

    @property
    def restricted_to_groups(self):

        if self.api and self.restricted_to_group_ids:
            return self.api._get_restricted_to_groups(
                self.restricted_to_group_ids)

    @restricted_to_groups.setter
    def restricted_to_groups(self, restricted_to_groups):
        if restricted_to_groups:
            self.restricted_to_group_ids = [o.id for o in restricted_to_groups]
            self._restricted_to_groups = restricted_to_groups

    @property
    def restricted_to_organizations(self):

        if self.api and self.restricted_to_organization_ids:
            return self.api._get_restricted_to_organizations(
                self.restricted_to_organization_ids)

    @restricted_to_organizations.setter
    def restricted_to_organizations(self, restricted_to_organizations):
        if restricted_to_organizations:
            self.restricted_to_organization_ids = [
                o.id for o in restricted_to_organizations
            ]
            self._restricted_to_organizations = restricted_to_organizations


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

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

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


class ArticleAttachment(BaseObject):
    def __init__(self,
                 api=None,
                 article_id=None,
                 content_type=None,
                 content_url=None,
                 file_name=None,
                 id=None,
                 inline=None,
                 size=None,
                 **kwargs):

        self.api = api
        self.article_id = article_id
        self.content_type = content_type
        self.content_url = content_url
        self.file_name = file_name
        self.id = id
        self.inline = inline
        self.size = size

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

    @property
    def article(self):

        if self.api and self.article_id:
            return self.api._get_article(self.article_id)

    @article.setter
    def article(self, article):
        if article:
            self.article_id = article.id
            self._article = article


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

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

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

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

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
    def updated(self):

        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated


class Label(BaseObject):
    def __init__(self,
                 api=None,
                 created_at=None,
                 id=None,
                 name=None,
                 updated_at=None,
                 url=None,
                 **kwargs):

        self.api = api
        self.created_at = created_at
        self.id = id
        self.name = name
        self.updated_at = updated_at
        self.url = url

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

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


class Post(BaseObject):
    def __init__(self,
                 api=None,
                 author_id=None,
                 closed=None,
                 comment_count=None,
                 created_at=None,
                 details=None,
                 featured=None,
                 follower_count=None,
                 html_url=None,
                 id=None,
                 pinned=None,
                 status=None,
                 title=None,
                 topic_id=None,
                 updated_at=None,
                 url=None,
                 vote_count=None,
                 vote_sum=None,
                 **kwargs):

        self.api = api
        self.author_id = author_id
        self.closed = closed
        self.comment_count = comment_count
        self.created_at = created_at
        self.details = details
        self.featured = featured
        self.follower_count = follower_count
        self.html_url = html_url
        self.id = id
        self.pinned = pinned
        self.status = status
        self.title = title
        self.topic_id = topic_id
        self.updated_at = updated_at
        self.url = url
        self.vote_count = vote_count
        self.vote_sum = vote_sum

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

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
    def topic(self):

        if self.api and self.topic_id:
            return self.api._get_topic(self.topic_id)

    @topic.setter
    def topic(self, topic):
        if topic:
            self.topic_id = topic.id
            self._topic = topic

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

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

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


class Subscription(BaseObject):
    def __init__(self,
                 api=None,
                 content_id=None,
                 created_at=None,
                 id=None,
                 locale=None,
                 updated_at=None,
                 url=None,
                 user_id=None,
                 **kwargs):

        self.api = api
        self.content_id = content_id
        self.created_at = created_at
        self.id = id
        self.locale = locale
        self.updated_at = updated_at
        self.url = url
        self.user_id = user_id

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

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
    def user(self):

        if self.api and self.user_id:
            return self.api._get_user(self.user_id)

    @user.setter
    def user(self, user):
        if user:
            self.user_id = user.id
            self._user = user


class Topic(BaseObject):
    def __init__(self,
                 api=None,
                 community_id=None,
                 created_at=None,
                 description=None,
                 follower_count=None,
                 html_url=None,
                 id=None,
                 name=None,
                 position=None,
                 updated_at=None,
                 url=None,
                 user_segment_id=None,
                 **kwargs):

        self.api = api
        self.community_id = community_id
        self.created_at = created_at
        self.description = description
        self.follower_count = follower_count
        self.html_url = html_url
        self.id = id
        self.name = name
        self.position = position
        self.updated_at = updated_at
        self.url = url
        self.user_segment_id = user_segment_id

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

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


class Translation(BaseObject):
    def __init__(self,
                 api=None,
                 body=None,
                 created_at=None,
                 created_by_id=None,
                 draft=None,
                 hidden=None,
                 html_url=None,
                 id=None,
                 locale=None,
                 outdated=None,
                 source_id=None,
                 source_type=None,
                 title=None,
                 updated_at=None,
                 updated_by_id=None,
                 url=None,
                 **kwargs):

        self.api = api
        self.body = body
        self.created_at = created_at
        self.created_by_id = created_by_id
        self.draft = draft
        self.hidden = hidden
        self.html_url = html_url
        self.id = id
        self.locale = locale
        self.outdated = outdated
        self.source_id = source_id
        self.source_type = source_type
        self.title = title
        self.updated_at = updated_at
        self.updated_by_id = updated_by_id
        self.url = url

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

    @property
    def created(self):

        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, created):
        if created:
            self.created_at = created

    @property
    def created_by(self):

        if self.api and self.created_by_id:
            return self.api._get_user(self.created_by_id)

    @created_by.setter
    def created_by(self, created_by):
        if created_by:
            self.created_by_id = created_by.id
            self._created_by = created_by

    @property
    def updated(self):

        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated

    @property
    def updated_by(self):

        if self.api and self.updated_by_id:
            return self.api._get_user(self.updated_by_id)

    @updated_by.setter
    def updated_by(self, updated_by):
        if updated_by:
            self.updated_by_id = updated_by.id
            self._updated_by = updated_by


class UserSegment(BaseObject):
    def __init__(self,
                 api=None,
                 built_in=None,
                 created_at=None,
                 group_ids=None,
                 id=None,
                 name=None,
                 organization_ids=None,
                 tags=None,
                 updated_at=None,
                 user_type=None,
                 **kwargs):

        self.api = api
        self.built_in = built_in
        self.created_at = created_at
        self.group_ids = group_ids
        self.id = id
        self.name = name
        self.organization_ids = organization_ids
        self.tags = tags
        self.updated_at = updated_at
        self.user_type = user_type

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

    @property
    def created(self):

        if self.created_at:
            return dateutil.parser.parse(self.created_at)

    @created.setter
    def created(self, created):
        if created:
            self.created_at = created

    @property
    def groups(self):

        if self.api and self.group_ids:
            return self.api._get_groups(self.group_ids)

    @groups.setter
    def groups(self, groups):
        if groups:
            self.group_ids = [o.id for o in groups]
            self._groups = groups

    @property
    def organizations(self):

        if self.api and self.organization_ids:
            return self.api._get_organizations(self.organization_ids)

    @organizations.setter
    def organizations(self, organizations):
        if organizations:
            self.organization_ids = [o.id for o in organizations]
            self._organizations = organizations

    @property
    def updated(self):

        if self.updated_at:
            return dateutil.parser.parse(self.updated_at)

    @updated.setter
    def updated(self, updated):
        if updated:
            self.updated_at = updated


class Vote(BaseObject):
    def __init__(self,
                 api=None,
                 created_at=None,
                 id=None,
                 item_id=None,
                 item_type=None,
                 updated_at=None,
                 url=None,
                 user_id=None,
                 value=None,
                 **kwargs):

        self.api = api
        self.created_at = created_at
        self.id = id
        self.item_id = item_id
        self.item_type = item_type
        self.updated_at = updated_at
        self.url = url
        self.user_id = user_id
        self.value = value

        for key, value in kwargs.items():
            setattr(self, key, value)

        for key in self.to_dict():
            if getattr(self, key) is None:
                try:
                    self._dirty_attributes.remove(key)
                except KeyError:
                    continue

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
    def user(self):

        if self.api and self.user_id:
            return self.api._get_user(self.user_id)

    @user.setter
    def user(self, user):
        if user:
            self.user_id = user.id
            self._user = user
