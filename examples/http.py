'''An example of how to use tornado_prof in a Tornado HTTP server application
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
