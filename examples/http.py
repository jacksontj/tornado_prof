'''An example of how to use tornado_prof in a Tornado HTTP server application

# Example /metrics output
    {
        "http.py:get:40": {
            "count": 1,
            "max": 0.0003428459167480469,
            "sum": 0.0003428459167480469
        },
        "http.py:good_coroutine:27": {
            "count": 2,
            "max": 0.00012302398681640625,
            "sum": 0.0002009868621826172
        },
        "http.py:bad_coroutine:32": {
            "count": 1,
            "max": 0.5006809234619141,
            "sum": 0.5006809234619141
        },
        "http.py:get:53": {
            "count": 2,
            "max": 0.5009949207305908,
            "sum": 0.5012478828430176
        },
        "http.py:complete:22": {
            "count": 1,
            "max": 5.1021575927734375e-05,
            "sum": 5.1021575927734375e-05
        },
        "/usr/lib/python/site-packages/tornado/gen.py:<lambda>:915": {
            "count": 1,
            "max": 5.1021575927734375e-05,
            "sum": 5.1021575927734375e-05
        },
        "/usr/lib/python/site-packages/tornado/http1connection.py:_server_request_loop:713": {
            "count": 4,
            "max": 0.00034499168395996094,
            "sum": 0.0008280277252197266
        },
        "/usr/lib/python/site-packages/tornado/http1connection.py:_read_message:153": {
            "count": 5,
            "max": 0.002012014389038086,
            "sum": 0.0037462711334228516
        },
        "/usr/lib/python/site-packages/tornado/ioloop.py:_run:1037": {
            "count": 8,
            "max": 0.002833127975463867,
            "sum": 0.02073216438293457
        },
        "/usr/lib/python/site-packages/tornado/web.py:_execute:1430": {
            "count": 1,
            "max": 0.0006561279296875,
            "sum": 0.0006561279296875
        }

    }
'''

import time
import json
import sys

import tornado_prof.ioloop
import tornado_prof.coroutine

import tornado.ioloop
import tornado.web

# Configure tornado to use the profiling IOLoop
tornado.ioloop.IOLoop.configure(tornado_prof.ioloop.ProfilingIOLoop)

# If we want timing information for the initial call into a coroutine (before the first yield)
# then we need to do this
tornado_prof.coroutine.monkey_patch()


@tornado.gen.coroutine
def complete():
    raise tornado.gen.Return('Hello, world')


@tornado.gen.coroutine
def good_coroutine(sleep=1):
    yield tornado.gen.sleep(sleep)


@tornado.gen.coroutine
def bad_coroutine(sleep=0.5):
    time.sleep(sleep)


class MetricsHandler(tornado.web.RequestHandler):
    """A basic json HTTP metrics endpoint to look at profiling information at
    """
    @tornado.gen.coroutine
    def get(self):
        metrics = tornado.ioloop.IOLoop.current().get_timings()
        json_metrics = {}
        for k, v in metrics.iteritems():
            json_metrics[':'.join((str(kitem) for kitem in k))] = v
        self.set_header('content-type', 'application/json')
        self.write(json.dumps(json_metrics))


class MainHandler(tornado.web.RequestHandler):
    """Simple handler which will call a few coroutines on each request
    """
    @tornado.gen.coroutine
    def get(self):
        yield good_coroutine()
        yield bad_coroutine()
        ret = yield complete()
        self.write(ret)


def make_app():
    """A simplistic app that will do some terrible things
    """
    return tornado.web.Application([
        (r"/metrics", MetricsHandler),
        (r"/", MainHandler),
    ], debug=True)


if __name__ == '__main__':
    app = make_app()
    app.listen(int(sys.argv[1]))
    tornado.ioloop.IOLoop.current().start()
