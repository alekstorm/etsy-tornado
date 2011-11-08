# etsy-tornado
Python wrapper for the Etsy API based on Tornado's IOLoop

Based on mcfunley/etsy-python, by Dan McKinley - dan@etsy.com - [http://mcfunley.com](http://mcfunley.com)

## Installation

The simplest way to install the module is using 
[setuptools](http://pypi.python.org/pypi/setuptools).

```
$ easy_install etsy-tornado
```

To install from source, extract the tarball and use the following commands.

```
$ python setup.py build
$ python setup.py install
```

## Simple Example

To use, first [register for an Etsy developer key](http://developer.etsy.com/).
Below is an example session. 

```python
from etsy import EtsyV2, Association, env
from tornado import gen
from tornado.ioloop import IOLoop

@gen.engine
def example():
    api = yield gen.Task(EtsyV2, 'YOUR-API-KEY-HERE', env=env.ProductionEnv)
    listings = yield gen.Task(
                   api.findAllListingActive,
                   keywords='candle',
                   limit=1,
                   fields=['title','price'],
                   includes=[Association('MainImage', fields=['url_75x75'])])
    print listings[0]
    io_loop.stop()

io_loop = IOLoop.instance()
io_loop.add_callback(example)
io_loop.start()
```

See also [this blog post](http://codeascraft.etsy.com/2010/04/22/announcing-etsys-new-api/)
on Code as Craft.


## Tests

This package comes with a reasonably complete unit test suite. In order to run
the tests, use:

```
$ python setup.py test
```

Some of the tests (those that actually call the Etsy API) require your API key
to be locally configured. See the Configuration section, above.


## Version History

### Version 0.4
* Rewrote to use non-blocking calls to the Etsy API through Tornado's IOLoop.
* Removed type-checking in favor of native Python function signature validation.
* Removed method table cache.
* Removed API key file storage.


### Version 0.3.1
* Allowing Python Longs to be passed for parameters declared as "integers" by the API 
  (thanks to [Marc Abramowitz](http://marc-abramowitz.com)). 


### Version 0.3 
* Support for Etsy API v2 thanks to [Marc Abramowitz](http://marc-abramowitz.com). 
* Removed support for now-dead Etsy API v1. 


### Version 0.2.1 
* Added a cache for the method table json.
* Added a logging facility.


### Version 0.2 - 05-31-2010
* Added local configuration (~/.etsy) to eliminate cutting & pasting of api keys.
* Added client-side type checking for parameters.
* Added support for positional arguments.
* Added a test suite.
* Began differentiation between API versions.
* Added module to PyPI. 

### Version 0.1 - 05-24-2010 
Initial release
