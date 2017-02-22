import types
import time
import functools

import tornado.ioloop
import tornado.gen

import tornado_prof.ioloop


def coroutine(func):
    """Replacement coroutine decorator which times the initial call
    """
    wrapped = tornado.gen._make_coroutine_wrapper(func, True)
    ioloop = tornado.ioloop.IOLoop.current()
    # If this isn't a ProfilingIOLoop -- lets do nothing
    if not isinstance(ioloop, tornado_prof.ioloop.ProfilingIOLoop):
        return wrapped

    @functools.wraps(wrapped)
    def wrapper(*args, **kwargs):
        if not ioloop.timing_enabled:
            return wrapped(*args, **kwargs)
        start = time.time()
        try:
            ret = wrapped(*args, **kwargs)
            return ret
        finally:
            took = time.time() - start
            key = (
                func.func_code.co_filename,
                func.func_code.co_name,
                func.func_code.co_firstlineno,
            )

            # TODO: store method?
            # Store the metrics
            try:
                ioloop._timing[key]['sum'] += took
                ioloop._timing[key]['count'] += 1
                ioloop._timing[key]['max'] = max(ioloop._timing[key]['max'], took)
            except KeyError:
                ioloop._timing[key] = {'sum': took, 'count': 1, 'max': took}

    return wrapper


def monkey_patch():
    """Monkey patch tornado.gen.coroutine to use the timing coroutine
    """
    tornado.gen.coroutine = coroutine
