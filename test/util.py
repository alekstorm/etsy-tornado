from tornado.testing import AsyncTestCase

def ignore(*args, **kwargs):
    pass

class EtsyTestCase(AsyncTestCase):
    def assertRaises(self, cls, f, *args, **kwargs):
        try:
            f(*args, **kwargs)
        except cls, e:
            return e.message
        else:
            name = cls.__name__ if hasattr(cls, '__name__') else str(cls)
            raise self.failureException, "%s not raised" % name
