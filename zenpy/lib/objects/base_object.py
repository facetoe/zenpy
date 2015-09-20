__author__ = 'facetoe'

class BaseObject(object):
	def to_dict(self):
		copy_dict = self.__dict__.copy()
		for key in copy_dict.keys():
			if copy_dict[key] is None:
				del copy_dict[key]
				continue

			if key.startswith('_'):
				print key
				print type(copy_dict[key])
				copy_dict[key[1:]] = copy_dict[key]
				del copy_dict[key]
		return copy_dict
