from __future__ import with_statement
from StringIO import StringIO
from tornado import gen
from tornado.httpclient import HTTPRequest, HTTPResponse

from etsy import EtsyV2
from util import EtsyTestCase, ignore

# TODO associations tests

class MockAPI(EtsyV2):
    def __init__(self, *args, **kwargs):
        EtsyV2.__init__(self, callback=ignore, *args, **kwargs)

    def _get_method_table(self, callback):
        callback([{
            'name': 'testMethod',
            'uri': '/test/:ps_arr_str',
            'http_method': 'GET',
            'params': {
                'ps_arr_str': 'array(string)',
                'kw_string': 'string',
                'kw_int': 'int',
                'kw_float': 'float',
                'kw_array_int': 'array(int)',
                'kw_enum': 'enum(foo, bar, baz)',
                'kw_unknown': 'unknown type',
            },
            'type': 'echo',
            'description': 'test method'
        }])

    def _fetch_resource(self, url, http_method, params, callback):
        callback([{
            'url': url,
            'http_method': http_method,
            'params': params,
        }])


class CoreTests(EtsyTestCase):
    def setUp(self):
        super(CoreTests, self).setUp()
        self.app = MockAPI(api_key='apikey')

    def test_method_created(self):
        self.assertTrue(getattr(self.app, 'testMethod', None) is not None)

    @gen.engine
    def test_positional_argument_in_url(self):
        result = (yield gen.Task(self.app.testMethod, ps_arr_str=['a']))[0]
        self.assertEquals(result['url'], '/test/a')

    @gen.engine
    def test_positional_argument_array_commas_in_url(self):
        result = (yield gen.Task(self.app.testMethod, ps_arr_str=['a','b']))[0]
        self.assertEquals(result['url'], '/test/a,b')

    def test_invalid_empty_positional_argument_array(self):
        msg = self.assertRaises(ValueError, self.app.testMethod, ps_arr_str=[], callback=ignore)
        self.assertEqual(msg, "Positional argument 'ps_arr_str' must not be an empty array")

    @gen.engine
    def test_http_method_match(self):
        result = (yield gen.Task(self.app.testMethod, ps_arr_str=['a']))[0]
        self.assertEquals(result['http_method'], 'GET')

    @gen.engine
    def test_keyword_argument_in_params(self):
        result = (yield gen.Task(self.app.testMethod, ps_arr_str=['a'], kw_int=5))[0]
        self.assertTrue('kw_int' in result['params'])
        self.assertEquals(result['params']['kw_int'], 5)

    def test_docstring_set(self):
        self.assertEquals(self.app.testMethod.__doc__, 'test method')
