from unittest import TestCase

from zenpy.lib.api_objects import Ticket, Comment
from zenpy.lib.proxy import ProxyList, ProxyDict


class TestProxyList(TestCase):
    __test__ = True

    def setUp(self):
        self.test_element = Comment()
        self.test_object = Ticket(comments=ProxyList([self.test_element]))
        self.attribute_name = 'comments'
        self.proxy_list = getattr(self.test_object, self.attribute_name)
        self.test_object._clean_dirty()
        self.proxy_list._clean_dirty()

    def tearDown(self):
        self.test_object._clean_dirty()
        self.proxy_list._clean_dirty()

    def test_list_clean_dirty(self):
        self.proxy_list[0] = "THING"
        self._assert_dirty()
        self.proxy_list._clean_dirty()
        self.assertFalse(self.proxy_list._dirty)

    def test_object_clean_dirty(self):
        self.proxy_list[0] = "THING"
        self._assert_dirty()
        self.test_object._clean_dirty()
        self.assertNotIn(self.attribute_name, self.test_object.to_dict(serialize=True))

    def test_proxy_list_assign(self):
        self.proxy_list[0] = True
        self._assert_dirty()

    def test_proxy_list_access_modification(self):
        element = self.proxy_list[0]
        element.modified = True
        self._assert_dirty()

    def test_proxy_list_append(self):
        self.proxy_list.append("THING")
        self._assert_dirty()

    def test_proxy_list_pop(self):
        self.proxy_list.pop()
        self._assert_dirty()

    def test_proxy_list_clear(self):
        # Doesn't exist in 2.7
        if hasattr(self.proxy_list, 'clear'):
            self.proxy_list.clear()
            self._assert_dirty()

    def test_proxy_list_extend(self):
        self.proxy_list.extend([1, 2, 3])
        self._assert_dirty()

    def test_proxy_list_remove(self):
        self.proxy_list.remove(self.test_element)
        self._assert_dirty()

    def test_proxy_list_insert(self):
        self.proxy_list.insert(0, 1)
        self._assert_dirty()

    def test_proxy_list_del(self):
        del self.proxy_list[0]
        self._assert_dirty()

    def test_proxy_list_iter_modification(self):
        for item in self.proxy_list:
            item.modified = True
        self._assert_dirty()

    def test_list_access_wrapped(self):
        self.proxy_list.append([])
        item = self.proxy_list[-1]
        self.assertIsInstance(item, ProxyList)

    def test_dict_access_wrapped(self):
        self.proxy_list.append({})
        item = self.proxy_list[-1]
        self.assertIsInstance(item, ProxyDict)

    def test_zenpy_object_wrapped(self):
        item = self.proxy_list[0]
        self.assertTrue(callable(item._dirty_callback))

    def _assert_dirty(self):
        self.assertTrue(self.proxy_list._dirty)
        self.assertIn(self.attribute_name, self.test_object.to_dict(serialize=True))


class TestProxyDict(TestCase):
    __test__ = True

    def setUp(self):
        self.test_object = Ticket(comments=ProxyDict(dict(comment=Comment(),
                                                          list=[1, 3, 4],
                                                          dict={1: 2, 3: 4})))
        self.attribute_name = 'comments'
        self.proxy_dict = getattr(self.test_object, self.attribute_name)
        self.proxy_dict._clean_dirty()
        self.test_object._clean_dirty()

    def test_proxy_dict_assign(self):
        self.proxy_dict['things'] = True
        self._assert_dirty()

    def test_proxy_dict_del(self):
        del self.proxy_dict['comment']
        self._assert_dirty()

    def test_proxy_dict_update(self):
        self.proxy_dict.update({10: 10})
        self._assert_dirty()

    def test_proxy_dict_pop(self):
        self.proxy_dict.pop(self.attribute_name)
        self._assert_dirty()

    def test_proxy_dict_popitem(self):
        self.proxy_dict.popitem()
        self._assert_dirty()

    def test_proxy_dict_clear(self):
        self.proxy_dict.clear()
        self._assert_dirty()

    def test_proxy_dict_wraps_list(self):
        some_list = self.proxy_dict['list']
        self.assertIsInstance(some_list, ProxyList)

    def test_proxy_list_wraps_dict(self):
        some_dict = self.proxy_dict['dict']
        self.assertIsInstance(some_dict, ProxyDict)

    def test_proxy_dict_wraps_zenpy_object(self):
        comment = self.proxy_dict['comment']
        self.assertTrue(callable(comment._dirty_callback))

    def _assert_dirty(self):
        self.assertTrue(self.proxy_dict._dirty)
        self.assertIn(self.attribute_name, self.test_object.to_dict(serialize=True))
