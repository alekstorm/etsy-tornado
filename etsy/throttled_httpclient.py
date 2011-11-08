from collections import deque
from datetime import timedelta
from tornado import gen
from tornado.simple_httpclient import SimpleAsyncHTTPClient

# TODO testing - simulation

class ThrottledAsyncHTTPClient(SimpleAsyncHTTPClient):
    def initialize(self, io_loop=None, max_clients=10, period=timedelta(seconds=1), **kwargs):
        SimpleAsyncHTTPClient.initialize(self, io_loop=io_loop, max_clients=max_clients, **kwargs)
        self.period = period
        self.available_requests = max_clients
        self.request_queue = deque()

    @gen.engine
    def fetch(self, request, callback, **kwargs):
        self.request_queue.append((request, callback, kwargs))
        while self.available_requests > 0 and len(self.request_queue) > 0:
            request, callback, kwargs = self.request_queue.popleft()
            SimpleAsyncHTTPClient.fetch(self, request, callback, **kwargs)
            self.available_requests -= 1
            yield gen.Task(self.io_loop.add_timeout, self.period)
            self.available_requests += 1
