__author__ = 'facetoe'


class BaseObject(object):
    def to_dict(self):
        copy_dict = self.__dict__.copy()
        for key in copy_dict.keys():
            if copy_dict[key] is None:
                del copy_dict[key]
                continue

            if key.startswith('_'):
                copy_dict[key[1:]] = copy_dict[key]
                del copy_dict[key]
        return copy_dict

    def __str__(self):
        if hasattr(self, 'id'):
            return "%s(%s)" % (self.__class__.__name__, self.id)
        else:
            return "%s()" % self.__class__.__name__
