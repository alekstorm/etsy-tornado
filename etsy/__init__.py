from __future__ import with_statement
from datetime import timedelta
try:
    import simplejson as json
except ImportError:
    import json
import logging
import re
from tornado import gen
from tornado.ioloop import IOLoop
from tornado.template import Template
from urllib import urlencode

from _util import encode_multipart_formdata
from env import SandboxEnv
from throttled_httpclient import ThrottledAsyncHTTPClient

__version__ = '0.4'
__author__ = 'Alek Storm, Dan McKinley'
__copyright__ = 'Copyright 2011, Alek Storm. Copyright 2010, Etsy Inc.'
__license__ = 'GPL v3'
__email__ = 'alek.storm@gmail.com'

logger = logging.getLogger('etsy')

# TODO required non-url args
# TODO declarative method table assertions

class EtsyV2(object):
    def __init__(self, api_key, callback, env=SandboxEnv, oauth_client=None, io_loop=None):
        """
        Parameters:
            io_loop      - An IO loop to use for method calls.

        Example method specification:
            {
                'name': 'createListing',
                'uri': '/listings',
                'visibility': 'private',
                'http_method': 'POST',
                'params': {
                    'tags': 'array(string)',
                    'price': 'float',
                    'title': 'string',
                    'quantity': 'int',
                },
                'defaults': {
                    'materials': None,
                    'shop_section_id': None
                },
                'type': 'Listing',
                'description': 'Creates a new Listing'
            }
        """

        self.http_client = ThrottledAsyncHTTPClient(max_clients=5, period=timedelta(seconds=1), io_loop=io_loop)
        self.api_key = api_key
        self.env = env
        self.oauth_client = oauth_client

        logger.info('Creating Etsy API, base url: %s', self.env.api_url)

        self._compiled_methods = {}
        self._methods = {}
        def methods_callback(methods):
            logger.info('Loaded method table: %r', methods)
            self._methods = dict([(method['name'], method) for method in methods])
            callback(self)
        self._get_method_table(methods_callback)

    def __getattr__(self, name):
        method = self._compiled_methods.get(name, None)
        if method:
            return method

        spec = self._methods[name]
        uri = spec['uri']
        positionals = set(re.findall(':([^/]+)', uri))

        for p in positionals:
            uri = re.sub(':%s(?=/|$)' % p, '%%(%s)s' % p, uri)
        keywords = set(spec['params'].keys()) - positionals

        code = Template("""def compiled({%for arg in positionals%}{{arg}},{%end%} callback, {%for arg in keywords%}{{arg}}=None,{%end%} fields=None, includes=None, api_key=None):
                {% for arg in positionals %}
                    {% if spec['params'][arg].startswith('array') %}
                if {{arg}} is not None and len({{arg}}) == 0:
                    raise ValueError("Positional argument '{{arg}}' must not be an empty array")
                    {% end %}
                {% end %}
                {% for arg in positionals|keywords %}
                    {% if spec['params'][arg].startswith('array') %}
                if {{arg}} is not None:
                    {{arg}} = ','.join([str(arg) for arg in {{arg}}])
                    {% end %}
                {% end %}

                kwargs = { {{param_dict(keywords)}} }
                kwargs['api_key'] = api_key or api.api_key
                if fields:
                    kwargs['fields'] = ','.join(fields)
                if includes:
                    kwargs['includes'] = ','.join([str(include) for include in includes])
                return api._fetch_resource(
                    '{{uri}}' % { {{param_dict(positionals)}} },
                    '{{spec['http_method']}}',
                    dict([(name,value) for name,value in kwargs.iteritems() if value is not None]),
                    callback=callback)"""
        ).generate(
            positionals=positionals,
            keywords=keywords,
            spec=spec,
            uri=uri,
            param_dict=lambda params: ','.join(["'%s':%s" % (arg,arg) for arg in params])
        )

        namespace = {'api': self}
        exec code in namespace
        compiled = namespace['compiled']
        compiled.__doc__ = spec['description']
        self._compiled_methods[name] = compiled
        return compiled


    def _get_method_table(self, callback):
        self._fetch_resource('/', 'GET', {'api_key': self.api_key}, callback)


    def _fetch_url(self, url, http_method, content_type, body, callback):
        logger.info("Fetching url: %r, method: %r, body: %r", url, http_method, body)
        headers = {'Content-Type': content_type} if content_type else {}
        if self.oauth_client is not None:
            self.oauth_client.do_oauth_request(url, http_method, content_type, body, callback)
        else:
            self.http_client.fetch(self.env.api_url+url, callback,
                method=http_method,
                headers=headers,
                body=body)


    @gen.engine
    def _fetch_resource(self, url, http_method, params, callback):
        body = None
        content_type = None
        if http_method == 'GET':
            url = '%s?%s' % (url, urlencode(params))
        elif http_method == 'POST':
            fields = []
            files = []

            for name, value in params.iteritems():
                if hasattr(value, 'read'):
                    files.append((name, value.name, value.read()))
                else:
                    fields.append((name, str(value)))

            content_type, body = encode_multipart_formdata(fields, files)

        data = (yield gen.Task(self._fetch_url, url, http_method, content_type, body)).body

        logger.info('Data received: %r' % data)

        try:
            callback(json.loads(data)['results'])
        except json.JSONDecodeError:
            raise ValueError('Could not decode response from Etsy as JSON: %r' % data)


class Association(object):
    class Bounds(object):
        def __init__(self, limit, offset=None):
            self.limit = limit
            self.offset = offset

    def __init__(self, name, fields=None, scope=None, bounds=None, child=None):
        self.name = name
        self.fields = fields
        self.scope = scope
        self.bounds = bounds
        self.child = child

    def __str__(self):
        elems = [self.name]
        if self.fields is not None:
            elems.extend(['(', ','.join(self.fields), ')'])
        if self.scope is not None:
            elems.extend([':', self.scope])
        if self.bounds is not None:
            elems.extend([':', str(self.bounds.limit)])
            if self.bounds.offset is not None:
                elems.extend([':', str(self.bounds.offset)])
        if self.child is not None:
            elems.extend(['/', str(self.child)])
        return ''.join(elems)
