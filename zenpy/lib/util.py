import re

FIRST_CAP_REGEX = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP_REGEX = re.compile('([a-z0-9])([A-Z])')


def to_snake_case(name):
    s1 = FIRST_CAP_REGEX.sub(r'\1_\2', name)
    return ALL_CAP_REGEX.sub(r'\1_\2', s1).lower()


def is_timezone_aware(datetime_obj):
    """
    Determine whether or not a given datetime object is timezone aware.
    """
    return datetime_obj.tzinfo is not None and datetime_obj.tzinfo.utcoffset(datetime_obj) is not None


def is_iterable_but_not_string(obj):
    """
    Determine whether or not obj is iterable but not a string (eg, a list, set, tuple etc).
    """
    return hasattr(obj, '__iter__') and not isinstance(obj, str) and not isinstance(obj, bytes)


def as_singular(result_key):
    """
    Given a result key, return in the singular form
    """
    if result_key.endswith('ies'):
        return re.sub('ies$', 'y', result_key)
    elif result_key.endswith('s'):
        return result_key[:-1]
    else:
        return result_key


def as_plural(result_key):
    """
    Given a result key, return in the plural form.
    """
    # Not at all guaranteed to work in all cases...
    if result_key.endswith('y'):
        return re.sub("y$", "ies", result_key)
    elif not result_key.endswith('s'):
        return result_key + 's'
    else:
        return result_key
